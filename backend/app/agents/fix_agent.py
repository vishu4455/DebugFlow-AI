import structlog
from app.services.llm_service import call_gemini

log = structlog.get_logger()

SCHEMA = """{
  "title": "short fix title",
  "steps": [
    {
      "step_num": 1,
      "action": "what to do",
      "code_hint": "optional SQL/Python/bash snippet or null",
      "estimated_time": "e.g. '5 min' or null"
    }
  ],
  "estimated_time": "total estimated fix time",
  "validation_checks": [
    {"check": "check description", "result": "pass|warn|fail", "note": "optional detail"}
  ],
  "rollback_plan": "1-2 sentence rollback strategy",
  "preventive_measures": ["list of 2-4 preventive recommendations"]
}"""


class FixAgent:
    """
    Generates a validated, step-by-step remediation plan based on
    the error classification, dependency analysis, and raw logs.
    """

    async def run(
        self,
        logs: str,
        classification: dict,
        dependency: dict,
        pipeline_id: str,
    ) -> dict:
        log.info("fix_agent.run", pipeline_id=pipeline_id)

        error_type = classification.get("error_type", "unknown")
        severity = classification.get("severity", "unknown")
        root_cause = classification.get("root_cause", "")
        blast_radius = dependency.get("blast_radius_summary", "")
        downstream = dependency.get("downstream", [])
        risk = dependency.get("risk", "unknown")

        downstream_str = "\n".join(
            f"  - {d.get('name')} ({d.get('impact')} impact)" for d in downstream
        )

        prompt = f"""You are a senior data engineering incident responder.

Generate a complete, actionable remediation plan for the following pipeline failure.

Pipeline ID: {pipeline_id}
Error Type: {error_type}
Severity: {severity}
Root Cause: {root_cause}
Blast Radius: {blast_radius}
Downstream at Risk:
{downstream_str or "  None identified"}
Overall Risk: {risk}

Raw Error Logs (excerpt):
---
{logs[:1500]}
---

Requirements:
- Write 3-7 numbered steps, each with a clear action
- Include SQL, Python, or bash code hints where relevant
- Add estimated time per step
- Add 3-5 validation checks (with pass/warn/fail status)
- Include a rollback plan
- Suggest 2-4 preventive measures to avoid recurrence
- Prioritize immediate stabilization before deep fixing"""

        return await call_gemini(prompt, SCHEMA)
