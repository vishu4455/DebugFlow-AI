"""Tests for output schema validators."""
import pytest
from app.utils.validators import (
    validate_classification,
    validate_dependency,
    validate_fix,
)


def test_valid_classification():
    data = {
        "error_type": "schema_mismatch",
        "severity": "high",
        "confidence": 85,
        "root_cause": "Column renamed upstream",
    }
    ok, msg = validate_classification(data)
    assert ok, msg


def test_invalid_severity():
    data = {"error_type": "oom", "severity": "catastrophic", "confidence": 80, "root_cause": "OOM"}
    ok, msg = validate_classification(data)
    assert not ok
    assert "severity" in msg


def test_invalid_confidence_range():
    data = {"error_type": "oom", "severity": "high", "confidence": 150, "root_cause": "OOM"}
    ok, msg = validate_classification(data)
    assert not ok
    assert "confidence" in msg


def test_unknown_error_type():
    data = {"error_type": "alien_invasion", "severity": "high", "confidence": 70, "root_cause": "Aliens"}
    ok, msg = validate_classification(data)
    assert not ok
    assert "error_type" in msg


def test_valid_dependency():
    data = {
        "upstream": [{"name": "crm_sync", "impact": "high"}],
        "downstream": [{"name": "finance_mart", "impact": "high"}],
        "risk": "high",
    }
    ok, msg = validate_dependency(data)
    assert ok, msg


def test_dependency_missing_node_name():
    data = {
        "upstream": [{"impact": "high"}],  # missing name
        "downstream": [],
        "risk": "low",
    }
    ok, msg = validate_dependency(data)
    assert not ok
    assert "name" in msg


def test_valid_fix():
    data = {
        "title": "Fix schema mismatch",
        "steps": [{"step_num": 1, "action": "Add alias"}],
        "estimated_time": "15 min",
    }
    ok, msg = validate_fix(data)
    assert ok, msg


def test_fix_empty_steps():
    data = {"title": "Fix", "steps": [], "estimated_time": "5 min"}
    ok, msg = validate_fix(data)
    assert not ok
    assert "step" in msg.lower()


def test_fix_missing_step_fields():
    data = {"title": "Fix", "steps": [{"step_num": 1}], "estimated_time": "5 min"}
    ok, msg = validate_fix(data)
    assert not ok
    assert "action" in msg
