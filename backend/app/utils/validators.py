# app/utils/validators.py
from typing import Any


REQUIRED_CLASSIFICATION_KEYS = {"error_type", "severity", "confidence", "root_cause"}
REQUIRED_DEPENDENCY_KEYS = {"upstream", "downstream", "risk"}
REQUIRED_FIX_KEYS = {"title", "steps", "estimated_time"}
VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_ERROR_TYPES = {
    "schema_mismatch", "oom", "timeout", "auth_failure",
    "missing_dependency", "data_quality", "network",
    "config_error", "syntax_error", "permission",
}


def validate_classification(data: dict) -> tuple[bool, str]:
    missing = REQUIRED_CLASSIFICATION_KEYS - set(data.keys())
    if missing:
        return False, f"Missing keys: {missing}"
    if data.get("severity") not in VALID_SEVERITIES:
        return False, f"Invalid severity: {data.get('severity')}"
    if data.get("error_type") not in VALID_ERROR_TYPES:
        return False, f"Unknown error_type: {data.get('error_type')}"
    conf = data.get("confidence")
    if not isinstance(conf, (int, float)) or not (0 <= conf <= 100):
        return False, "confidence must be 0-100"
    return True, "ok"


def validate_dependency(data: dict) -> tuple[bool, str]:
    missing = REQUIRED_DEPENDENCY_KEYS - set(data.keys())
    if missing:
        return False, f"Missing keys: {missing}"
    for node in data.get("upstream", []) + data.get("downstream", []):
        if "name" not in node or "impact" not in node:
            return False, "Each dependency node needs 'name' and 'impact'"
    return True, "ok"


def validate_fix(data: dict) -> tuple[bool, str]:
    missing = REQUIRED_FIX_KEYS - set(data.keys())
    if missing:
        return False, f"Missing keys: {missing}"
    steps = data.get("steps", [])
    if not steps:
        return False, "Fix must have at least one step"
    for step in steps:
        if "step_num" not in step or "action" not in step:
            return False, "Each step needs step_num and action"
    return True, "ok"
