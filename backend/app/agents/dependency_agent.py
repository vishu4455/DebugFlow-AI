import structlog
from app.services.llm_service import call_gemini

log = structlog.get_logger()

SCHEMA = """{
  "upstream": [
    {"name": "string", "type": "string", "status": "healthy|degraded|down|unknown", "impact": "high|medium|low"}
  ],
  "downstream": [
    {"name": "string", "type": "string", "status": "blocked|degraded|healthy|unknown", "impact": "high|medium|low"}
  ],
  "risk": "high|medium|low",
  "blast_radius_summary": "1 sentence",
  "slas_at_risk": ["array of strings"],
  "isolation_point": "string",
  "cascading_risk": "high|medium|low",
  "graph": {
    "nodes": [
      {"id": "string", "label": "string", "type": "pipeline|table|api|kafka|s3|dashboard|ml_model", "role": "failed|upstream|downstream", "impact": "high|medium|low|none"}
    ],
    "edges": [
      {"source": "string", "target": "string", "label": "string"}
    ]
  }
}"""


class DependencyAgent:
    async def run(self, pipeline_id: str, classification: dict, config: str | None = None) -> dict:
        log.info("dependency_agent.run", pipeline_id=pipeline_id)
        error_type = classification.get("error_type", "unknown")
        severity   = classification.get("severity", "unknown")

        prompt = f"""You are a data dependency graph analyzer.

Given a failed pipeline and its error classification, map all upstream sources
and downstream consumers, then produce a full dependency graph.

Pipeline ID: {pipeline_id}
Error Type: {error_type}
Severity: {severity}
Root Cause: {classification.get("root_cause", "")}

Config / Context:
{config or "No config provided — infer typical dependencies for this pipeline type"}

Instructions:
- List 2-5 upstream dependencies
- List 3-6 downstream consumers
- Build graph.nodes with ALL nodes. The failed pipeline itself has role="failed".
  Upstream nodes have role="upstream", downstream have role="downstream".
- Build graph.edges showing data flow. Upstream nodes point TO the failed pipeline.
  The failed pipeline points TO downstream nodes.
- Node IDs must be unique snake_case slugs.
- Assess blast radius, cascading risk, SLAs at risk, and isolation point."""

        return await call_gemini(prompt, SCHEMA)
