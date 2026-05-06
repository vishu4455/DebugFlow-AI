import structlog
from app.services.llm_service import call_gemini

log = structlog.get_logger()

SCHEMA = """{
  "pipeline_id": "string",
  "environment": "string (prod/staging/dev)",
  "last_successful_run": "ISO8601 string or null",
  "fail_count_7d": "integer",
  "avg_runtime_min": "float",
  "data_volume": "string e.g. '2.3GB' or '1.2M rows'",
  "schedule": "string e.g. 'daily 03:00 UTC'",
  "owner": "string team or person",
  "tags": ["array", "of", "strings"],
  "run_history": [
    {
      "run_id": "string",
      "status": "success|failed|running",
      "timestamp": "ISO8601",
      "duration_min": "float",
      "rows_processed": "integer"
    }
  ]
}"""


class MetadataAgent:
    """
    Fetches and synthesizes pipeline metadata and run history.
    Uses LLM to generate realistic metadata from pipeline ID + config.
    In production this would also call your metadata store / Airflow API.
    """

    async def run(self, pipeline_id: str, config: str | None = None) -> dict:
        log.info("metadata_agent.run", pipeline_id=pipeline_id)

        prompt = f"""You are a data platform metadata agent. Given the pipeline ID and optional config,
generate realistic pipeline metadata as if retrieved from a production metadata store.

Pipeline ID: {pipeline_id}
Config / Context:
{config or "No config provided"}

Infer realistic values for environment, schedule, team ownership, and recent run history
(last 5 runs). Include at least 1 failed run in history to reflect a real scenario.
Make the fail_count_7d consistent with the provided error context."""

        return await call_gemini(prompt, SCHEMA)
