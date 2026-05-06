# app/utils/parser.py
import re
import json
from typing import Any


def extract_json_from_text(text: str) -> dict | None:
    """
    Try to extract valid JSON from LLM text output that may contain
    markdown fences or extra prose.
    """
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strip ```json ... ``` fences
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    match = re.search(fence_pattern, text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find first { ... } block
    brace_pattern = r"\{[\s\S]*\}"
    match = re.search(brace_pattern, text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def truncate_logs(logs: str, max_chars: int = 4000) -> str:
    """Truncate log text to avoid token limit overflows."""
    if len(logs) <= max_chars:
        return logs
    half = max_chars // 2
    return logs[:half] + "\n... [truncated] ...\n" + logs[-half:]


def sanitize_pipeline_id(pipeline_id: str) -> str:
    """Remove characters that could cause issues in DB/cache keys."""
    return re.sub(r"[^\w\-\.]", "_", pipeline_id)[:128]
