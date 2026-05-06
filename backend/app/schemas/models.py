from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ─── Request ────────────────────────────────────────────────────────────────

class DebugRequest(BaseModel):
    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    error_logs: str = Field(..., description="Raw error log text")
    pipeline_config: Optional[str] = Field(None, description="YAML/JSON pipeline config")
    log_source: Optional[str] = Field(
        "inline", description="Source of logs: inline | airflow | s3"
    )

    model_config = {"json_schema_extra": {"example": {
        "pipeline_id": "etl_sales_daily_v2",
        "error_logs": "AnalysisException: Cannot resolve column 'user_id'",
        "pipeline_config": "upstream: [crm_sync] downstream: [finance_mart]",
        "log_source": "inline",
    }}}


# ─── Agent Result ────────────────────────────────────────────────────────────

class AgentResult(BaseModel):
    agent: str
    status: str  # success | error
    output: dict[str, Any]
    duration_ms: float
    error: Optional[str] = None


# ─── Classification ──────────────────────────────────────────────────────────

class ClassificationOutput(BaseModel):
    error_type: str
    severity: str  # critical | high | medium | low
    confidence: int  # 0-100
    root_cause: str
    indicators: list[str] = []
    affected_layer: Optional[str] = None


# ─── Dependency ──────────────────────────────────────────────────────────────

class DependencyNode(BaseModel):
    name: str
    type: Optional[str] = None
    status: Optional[str] = None
    impact: str  # high | medium | low


class DependencyOutput(BaseModel):
    upstream: list[DependencyNode]
    downstream: list[DependencyNode]
    risk: str
    blast_radius_summary: str
    slas_at_risk: list[str] = []


# ─── Fix ─────────────────────────────────────────────────────────────────────

class FixStep(BaseModel):
    step_num: int
    action: str
    code_hint: Optional[str] = None
    estimated_time: Optional[str] = None


class ValidationCheck(BaseModel):
    check: str
    result: str  # pass | warn | fail
    note: Optional[str] = None


class FixOutput(BaseModel):
    title: str
    steps: list[FixStep]
    estimated_time: str
    validation_checks: list[ValidationCheck] = []
    rollback_plan: Optional[str] = None
    preventive_measures: list[str] = []


# ─── Metadata ────────────────────────────────────────────────────────────────

class RunRecord(BaseModel):
    run_id: str
    status: str
    timestamp: str
    duration_min: float
    rows_processed: int


class MetadataOutput(BaseModel):
    pipeline_id: str
    environment: str
    last_successful_run: Optional[str]
    fail_count_7d: int
    avg_runtime_min: float
    data_volume: str
    schedule: str
    owner: str
    tags: list[str]
    run_history: list[RunRecord]


# ─── Response ────────────────────────────────────────────────────────────────

class DebugResponse(BaseModel):
    pipeline_id: str
    agent_results: dict[str, AgentResult]
    total_duration_ms: float
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PipelineStatusResponse(BaseModel):
    pipeline_id: str
    history: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
