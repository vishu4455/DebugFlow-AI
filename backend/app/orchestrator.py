import asyncio
import time
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.log_fetch_agent import LogFetchAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.classifier_agent import ClassifierAgent
from app.agents.dependency_agent import DependencyAgent
from app.agents.fix_agent import FixAgent
from app.schemas.models import DebugRequest, DebugResponse, AgentResult
from app.services.db import save_debug_result
from app.services.cache import get_cached, set_cached

log = structlog.get_logger()


class Orchestrator:
    """
    Central orchestrator that coordinates all agents in sequence:
    logs → metadata → classify → dependencies → fix
    """

    def __init__(self):
        self.log_fetcher = LogFetchAgent()
        self.metadata_agent = MetadataAgent()
        self.classifier = ClassifierAgent()
        self.dependency_analyzer = DependencyAgent()
        self.fix_generator = FixAgent()

    async def run(self, request: DebugRequest) -> DebugResponse:
        pipeline_id = request.pipeline_id
        cache_key = f"debug:{pipeline_id}:{hash(request.error_logs)}"

        cached = await get_cached(cache_key)
        if cached:
            log.info("orchestrator.cache_hit", pipeline_id=pipeline_id)
            return DebugResponse(**cached)

        log.info("orchestrator.start", pipeline_id=pipeline_id)
        start_total = time.time()
        agent_results: dict[str, AgentResult] = {}

        # Step 1: Fetch external logs (Airflow / S3)
        agent_results["log_fetch"] = await self._run_agent(
            "log_fetch",
            self.log_fetcher.run,
            pipeline_id=pipeline_id,
            source=request.log_source,
        )
        raw_logs = agent_results["log_fetch"].output.get("logs", request.error_logs)

        # Step 2: Metadata fetch + error classification run in parallel
        metadata_task = asyncio.create_task(
            self._run_agent(
                "metadata",
                self.metadata_agent.run,
                pipeline_id=pipeline_id,
                config=request.pipeline_config,
            )
        )
        classify_task = asyncio.create_task(
            self._run_agent(
                "classification",
                self.classifier.run,
                logs=raw_logs,
                pipeline_id=pipeline_id,
            )
        )
        agent_results["metadata"], agent_results["classification"] = await asyncio.gather(
            metadata_task, classify_task
        )

        # Step 3: Dependency analysis (needs classification result)
        agent_results["dependency"] = await self._run_agent(
            "dependency",
            self.dependency_analyzer.run,
            pipeline_id=pipeline_id,
            classification=agent_results["classification"].output,
            config=request.pipeline_config,
        )

        # Step 4: Fix generation (needs all prior context)
        agent_results["fix"] = await self._run_agent(
            "fix",
            self.fix_generator.run,
            logs=raw_logs,
            classification=agent_results["classification"].output,
            dependency=agent_results["dependency"].output,
            pipeline_id=pipeline_id,
        )

        total_ms = round((time.time() - start_total) * 1000, 2)
        log.info("orchestrator.complete", pipeline_id=pipeline_id, total_ms=total_ms)

        response = DebugResponse(
            pipeline_id=pipeline_id,
            agent_results=agent_results,
            total_duration_ms=total_ms,
            status="success",
        )

        await set_cached(cache_key, response.model_dump(), ttl=300)
        await save_debug_result(pipeline_id, response.model_dump())

        return response

    async def _run_agent(self, name: str, fn, **kwargs) -> AgentResult:
        start = time.time()
        log.info(f"agent.start", agent=name)
        try:
            output = await fn(**kwargs)
            duration_ms = round((time.time() - start) * 1000, 2)
            log.info(f"agent.success", agent=name, duration_ms=duration_ms)
            return AgentResult(
                agent=name,
                status="success",
                output=output,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = round((time.time() - start) * 1000, 2)
            log.error(f"agent.error", agent=name, error=str(exc))
            return AgentResult(
                agent=name,
                status="error",
                output={"error": str(exc)},
                duration_ms=duration_ms,
                error=str(exc),
            )
