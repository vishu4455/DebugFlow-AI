import json
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, before_log, after_log
import google.generativeai as genai
from app.core.config import settings

log = structlog.get_logger()

genai.configure(api_key=settings.GEMINI_API_KEY)

_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        temperature=0.2,
    ),
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def call_gemini(prompt: str, schema_hint: str = "") -> dict:
    """
    Call Gemini with strict JSON output and retry logic.
    Returns parsed dict or raises on failure.
    """
    full_prompt = f"{prompt}"
    if schema_hint:
        full_prompt += f"\n\nRespond ONLY with valid JSON matching this schema:\n{schema_hint}"

    log.debug("llm.call", prompt_len=len(full_prompt))
    response = _model.generate_content(full_prompt)
    raw = response.text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    parsed = json.loads(raw)
    log.debug("llm.success", keys=list(parsed.keys()) if isinstance(parsed, dict) else "array")
    return parsed


async def call_gemini_text(prompt: str) -> str:
    """Call Gemini for plain text response (no JSON enforcement)."""
    text_model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=genai.GenerationConfig(temperature=0.3),
    )
    response = text_model.generate_content(prompt)
    return response.text.strip()
