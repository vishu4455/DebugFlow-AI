"""
Tests for individual agents.
Run: pytest tests/ -v
"""
import pytest
from unittest.mock import AsyncMock, patch

# ─── Classifier Agent ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_classifier_returns_required_keys():
    mock_output = {
        "error_type": "schema_mismatch",
        "severity": "high",
        "confidence": 92,
        "root_cause": "Column user_id missing from schema",
        "indicators": ["AnalysisException", "user_id", "schema mismatch"],
        "affected_layer": "transform",
    }
    with patch("app.agents.classifier_agent.call_gemini", new=AsyncMock(return_value=mock_output)):
        from app.agents.classifier_agent import ClassifierAgent
        agent = ClassifierAgent()
        result = await agent.run(logs="fake logs", pipeline_id="test_pipeline")
        assert result["error_type"] == "schema_mismatch"
        assert result["severity"] == "high"
        assert 0 <= result["confidence"] <= 100


@pytest.mark.asyncio
async def test_classifier_handles_oom():
    mock_output = {
        "error_type": "oom",
        "severity": "critical",
        "confidence": 97,
        "root_cause": "GC overhead limit exceeded — executor ran out of heap memory",
        "indicators": ["OutOfMemoryError", "GC overhead", "executor died"],
        "affected_layer": "transform",
    }
    with patch("app.agents.classifier_agent.call_gemini", new=AsyncMock(return_value=mock_output)):
        from app.agents.classifier_agent import ClassifierAgent
        result = await ClassifierAgent().run(
            logs="java.lang.OutOfMemoryError: GC overhead limit exceeded",
            pipeline_id="spark_job"
        )
        assert result["error_type"] == "oom"
        assert result["severity"] == "critical"


# ─── Dependency Agent ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dependency_returns_upstream_downstream():
    mock_output = {
        "upstream": [{"name": "crm_sync", "type": "table", "status": "healthy", "impact": "high"}],
        "downstream": [{"name": "finance_mart", "type": "table", "status": "blocked", "impact": "high"}],
        "risk": "high",
        "blast_radius_summary": "Finance reporting blocked for the day",
        "slas_at_risk": ["Daily Revenue Report"],
        "isolation_point": "etl_sales_daily output table",
        "cascading_risk": "high",
    }
    with patch("app.agents.dependency_agent.call_gemini", new=AsyncMock(return_value=mock_output)):
        from app.agents.dependency_agent import DependencyAgent
        result = await DependencyAgent().run(
            pipeline_id="etl_sales",
            classification={"error_type": "schema_mismatch", "severity": "high", "root_cause": "Missing column"},
        )
        assert len(result["upstream"]) >= 1
        assert len(result["downstream"]) >= 1
        assert result["risk"] in ("high", "medium", "low")


# ─── Fix Agent ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fix_agent_produces_steps():
    mock_output = {
        "title": "Schema column rename fix",
        "steps": [
            {"step_num": 1, "action": "Add column alias", "code_hint": "SELECT uid AS user_id", "estimated_time": "5 min"},
            {"step_num": 2, "action": "Rerun pipeline", "code_hint": None, "estimated_time": "10 min"},
        ],
        "estimated_time": "15 min",
        "validation_checks": [
            {"check": "Schema matches target", "result": "pass", "note": None}
        ],
        "rollback_plan": "Revert SQL transformation to previous version",
        "preventive_measures": ["Add schema contract tests"],
    }
    with patch("app.agents.fix_agent.call_gemini", new=AsyncMock(return_value=mock_output)):
        from app.agents.fix_agent import FixAgent
        result = await FixAgent().run(
            logs="AnalysisException: Cannot resolve column user_id",
            classification={"error_type": "schema_mismatch", "severity": "high", "root_cause": "Column renamed"},
            dependency={"downstream": [{"name": "finance_mart", "impact": "high"}], "blast_radius_summary": "Finance blocked"},
            pipeline_id="etl_sales",
        )
        assert len(result["steps"]) >= 1
        assert "title" in result
        assert "estimated_time" in result


# ─── Metadata Agent ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_metadata_agent_returns_run_history():
    mock_output = {
        "pipeline_id": "etl_sales_daily_v2",
        "environment": "prod",
        "last_successful_run": "2025-04-28T03:10:00Z",
        "fail_count_7d": 3,
        "avg_runtime_min": 18.5,
        "data_volume": "2.3GB",
        "schedule": "daily 03:00 UTC",
        "owner": "data-platform-team",
        "tags": ["sales", "etl", "critical"],
        "run_history": [
            {"run_id": "run_001", "status": "failed", "timestamp": "2025-04-29T03:17:00Z", "duration_min": 5, "rows_processed": 0},
            {"run_id": "run_002", "status": "success", "timestamp": "2025-04-28T03:10:00Z", "duration_min": 18, "rows_processed": 1200000},
        ],
    }
    with patch("app.agents.metadata_agent.call_gemini", new=AsyncMock(return_value=mock_output)):
        from app.agents.metadata_agent import MetadataAgent
        result = await MetadataAgent().run(pipeline_id="etl_sales_daily_v2")
        assert result["fail_count_7d"] == 3
        assert len(result["run_history"]) >= 1
        assert result["environment"] == "prod"
