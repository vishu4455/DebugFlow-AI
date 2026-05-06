import structlog
from app.services.llm_service import call_gemini

log = structlog.get_logger()

SCHEMA = """{
  "error_type": "one of: schema_mismatch | oom | timeout | auth_failure | missing_dependency | data_quality | network | config_error | syntax_error | permission",
  "severity": "one of: critical | high | medium | low",
  "confidence": "integer 0-100",
  "root_cause": "1-2 sentence explanation",
  "indicators": ["list of 3-5 short indicator strings found in the logs"],
  "secondary_errors": ["optional secondary error types"],
  "affected_layer": "one of: ingestion | transform | load | orchestration"
}"""


class ClassifierAgent:
    """
    Analyzes error logs and classifies the failure type, severity,
    and root cause with a confidence score.
    """

    async def run(self, logs: str, pipeline_id: str) -> dict:
        log.info("classifier_agent.run", pipeline_id=pipeline_id)

        prompt = f"""You are an expert data engineering failure classifier.

Analyze the following pipeline error logs and classify the failure precisely.

Pipeline ID: {pipeline_id}

Error Logs:
---
{logs}
---

Instructions:
- Identify the PRIMARY error type from the allowed values
- Assess severity based on downstream business impact
- Provide a confidence score (higher = more certain)
- Extract specific indicators (exact error strings, class names, codes) from the logs
- Identify the layer where the failure occurred"""

        return await call_gemini(prompt, SCHEMA)
