"""Tests for the Orchestrator flow."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.orchestrator import Orchestrator
from app.schemas.models import DebugRequest, AgentResult


def make_agent_result(agent_name: str, output: dict) -> AgentResult:
    return AgentResult(agent=agent_name, status="success", output=output, duration_ms=100.0)


@pytest.mark.asyncio
async def test_orchestrator_full_flow():
    request = DebugRequest(
        pipeline_id="etl_test",
        error_logs="ERROR: Column user_id not found",
        log_source="inline",
    )

    fake_outputs = {
        "log_fetch": {"logs": "", "source": "inline", "status": "passthrough"},
        "metadata": {"pipeline_id": "etl_test", "fail_count_7d": 2, "run_history": []},
        "classification": {"error_type": "schema_mismatch", "severity": "high", "confidence": 90, "root_cause": "Column missing"},
        "dependency": {"upstream": [], "downstream": [], "risk": "medium", "blast_radius_summary": "Low impact"},
        "fix": {"title": "Add alias", "steps": [{"step_num": 1, "action": "Alias column"}], "estimated_time": "10 min"},
    }

    orch = Orchestrator()

    # Patch each agent's run method
    orch.log_fetcher.run = AsyncMock(return_value=fake_outputs["log_fetch"])
    orch.metadata_agent.run = AsyncMock(return_value=fake_outputs["metadata"])
    orch.classifier.run = AsyncMock(return_value=fake_outputs["classification"])
    orch.dependency_analyzer.run = AsyncMock(return_value=fake_outputs["dependency"])
    orch.fix_generator.run = AsyncMock(return_value=fake_outputs["fix"])

    with patch("app.orchestrator.get_cached", new=AsyncMock(return_value=None)), \
         patch("app.orchestrator.set_cached", new=AsyncMock()), \
         patch("app.orchestrator.save_debug_result", new=AsyncMock()):
        result = await orch.run(request)

    assert result.pipeline_id == "etl_test"
    assert result.status == "success"
    assert "classification" in result.agent_results
    assert result.agent_results["classification"].status == "success"
    assert result.agent_results["classification"].output["error_type"] == "schema_mismatch"


@pytest.mark.asyncio
async def test_orchestrator_handles_agent_error():
    """If one agent fails, orchestrator should still return a result with error status."""
    request = DebugRequest(
        pipeline_id="failing_pipeline",
        error_logs="Some error",
        log_source="inline",
    )

    orch = Orchestrator()
    orch.log_fetcher.run = AsyncMock(return_value={"logs": "", "source": "inline", "status": "passthrough"})
    orch.metadata_agent.run = AsyncMock(return_value={"pipeline_id": "x", "run_history": []})
    orch.classifier.run = AsyncMock(side_effect=Exception("Gemini API timeout"))
    orch.dependency_analyzer.run = AsyncMock(return_value={"upstream": [], "downstream": [], "risk": "low", "blast_radius_summary": ""})
    orch.fix_generator.run = AsyncMock(return_value={"title": "N/A", "steps": [], "estimated_time": "N/A"})

    with patch("app.orchestrator.get_cached", new=AsyncMock(return_value=None)), \
         patch("app.orchestrator.set_cached", new=AsyncMock()), \
         patch("app.orchestrator.save_debug_result", new=AsyncMock()):
        result = await orch.run(request)

    # Classification should be marked as error but result overall still returns
    assert result.agent_results["classification"].status == "error"
    assert "Gemini API timeout" in result.agent_results["classification"].error


@pytest.mark.asyncio
async def test_orchestrator_uses_cache():
    """Second call with same inputs should return cached result."""
    request = DebugRequest(
        pipeline_id="cached_pipeline",
        error_logs="OOM error",
        log_source="inline",
    )

    cached_data = {
        "pipeline_id": "cached_pipeline",
        "agent_results": {},
        "total_duration_ms": 1200.0,
        "status": "success",
        "created_at": "2025-04-29T12:00:00",
    }

    with patch("app.orchestrator.get_cached", new=AsyncMock(return_value=cached_data)):
        orch = Orchestrator()
        result = await orch.run(request)

    assert result.pipeline_id == "cached_pipeline"
