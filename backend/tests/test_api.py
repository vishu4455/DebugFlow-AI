"""
Integration tests for FastAPI endpoints.
Run: pytest tests/ -v
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.schemas.models import AgentResult


MOCK_AGENT_RESULT = AgentResult(
    agent="test",
    status="success",
    output={"key": "value"},
    duration_ms=120.0,
)

MOCK_DEBUG_RESPONSE = {
    "pipeline_id": "test_pipeline",
    "agent_results": {
        "log_fetch": MOCK_AGENT_RESULT.model_dump(),
        "metadata": MOCK_AGENT_RESULT.model_dump(),
        "classification": MOCK_AGENT_RESULT.model_dump(),
        "dependency": MOCK_AGENT_RESULT.model_dump(),
        "fix": MOCK_AGENT_RESULT.model_dump(),
    },
    "total_duration_ms": 3200.0,
    "status": "success",
    "created_at": "2025-04-29T12:00:00",
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.anyio
async def test_debug_failure_calls_orchestrator():
    from app.schemas.models import DebugResponse
    mock_response = DebugResponse(**MOCK_DEBUG_RESPONSE)

    with patch("app.main.Orchestrator") as MockOrch:
        instance = MockOrch.return_value
        instance.run = AsyncMock(return_value=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/debug-failure", json={
                "pipeline_id": "test_pipeline",
                "error_logs": "ERROR: Something went wrong",
                "log_source": "inline",
            })

    assert resp.status_code == 200
    body = resp.json()
    assert body["pipeline_id"] == "test_pipeline"
    assert body["status"] == "success"


@pytest.mark.anyio
async def test_debug_failure_requires_pipeline_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/debug-failure", json={
            "error_logs": "Some error",
            # pipeline_id missing
        })
    assert resp.status_code == 422  # Pydantic validation error


@pytest.mark.anyio
async def test_pipeline_status_endpoint():
    with patch("app.main.get_pipeline_history", new=AsyncMock(return_value=[])):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/pipeline-status", params={"pipeline_id": "etl_sales"})
    assert resp.status_code == 200
    assert resp.json()["pipeline_id"] == "etl_sales"
