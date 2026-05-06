"""
routers/feedback.py — User feedback on classification accuracy + fix usefulness.
Stores results in Postgres, exposes aggregate metrics.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user, require_role
from app.services.db import (
    save_feedback,
    get_feedback_metrics,
    get_all_feedback,
)

log = structlog.get_logger()
router = APIRouter(tags=["Feedback"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    pipeline_id: str
    debug_session_id: Optional[str] = None       # links to a debug result row
    classification_correct: Optional[bool] = None  # True = 👍, False = 👎, None = no opinion
    fix_useful: Optional[bool] = None
    actual_error_type: Optional[str] = None       # user correction
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    message: str


class MetricsResponse(BaseModel):
    total_feedback: int
    classification_accuracy_pct: Optional[float]
    fix_usefulness_pct: Optional[float]
    breakdown_by_error_type: dict
    last_updated: datetime


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    body: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """Submit 👍/👎 feedback on classification and/or fix quality."""
    if body.classification_correct is None and body.fix_useful is None:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of: classification_correct or fix_useful",
        )

    feedback_id = await save_feedback(
        pipeline_id=body.pipeline_id,
        session_id=body.debug_session_id,
        username=current_user.get("username", "anonymous"),
        classification_correct=body.classification_correct,
        fix_useful=body.fix_useful,
        actual_error_type=body.actual_error_type,
        comment=body.comment,
    )
    log.info(
        "feedback.submitted",
        pipeline_id=body.pipeline_id,
        classification_correct=body.classification_correct,
        fix_useful=body.fix_useful,
        user=current_user.get("username"),
    )
    return FeedbackResponse(id=feedback_id, message="Feedback recorded — thank you!")


@router.get("/feedback/metrics", response_model=MetricsResponse)
async def feedback_metrics(
    _admin: dict = Depends(require_role("admin")),
):
    """Aggregate feedback metrics — admin only."""
    metrics = await get_feedback_metrics()
    return MetricsResponse(**metrics)


@router.get("/feedback/all")
async def all_feedback(
    limit: int = 50,
    _admin: dict = Depends(require_role("admin")),
):
    """List raw feedback rows — admin only."""
    rows = await get_all_feedback(limit=limit)
    return {"feedback": rows}
