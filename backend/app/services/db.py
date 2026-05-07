"""
services/db.py — Async SQLAlchemy models + CRUD for:
  - DebugResult    (pipeline debug sessions)
  - FeedbackEntry  (user feedback / eval metrics)
"""

from __future__ import annotations

import json
import structlog
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    String, Text, DateTime, Float, Boolean, Integer,
    func, select, case
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.config import settings

log = structlog.get_logger()

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
class User(Base):
    __tablename__ = "users"

    id:              Mapped[int]  = mapped_column(primary_key=True)
    username:        Mapped[str]  = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str]  = mapped_column(String(255))
    role:            Mapped[str]  = mapped_column(String(50), default="user")
    disabled:        Mapped[bool] = mapped_column(Boolean, default=False)
    created_at:      Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DebugResult(Base):
    __tablename__ = "debug_results"

    id:               Mapped[int]   = mapped_column(primary_key=True)
    pipeline_id:      Mapped[str]   = mapped_column(String(255), index=True)
    status:           Mapped[str]   = mapped_column(String(50))
    result_json:      Mapped[str]   = mapped_column(Text)
    total_duration_ms: Mapped[float] = mapped_column(Float)
    error_type:       Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    severity:         Mapped[Optional[str]] = mapped_column(String(50),  nullable=True)
    created_at:       Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id:                     Mapped[int]  = mapped_column(primary_key=True)
    pipeline_id:            Mapped[str]  = mapped_column(String(255), index=True)
    session_id:             Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    username:               Mapped[str]  = mapped_column(String(255))
    classification_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    fix_useful:             Mapped[Optional[bool]]  = mapped_column(Boolean, nullable=True)
    actual_error_type:      Mapped[Optional[str]]   = mapped_column(String(100), nullable=True)
    comment:                Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    created_at:             Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("db.initialized")
    except Exception as e:
        log.warning("db.init_failed", error=str(e))


async def save_debug_result(pipeline_id: str, result: dict) -> Optional[int]:
    try:
        class_out = (
            result.get("agent_results", {})
            .get("classification", {})
            .get("output", {})
        )
        async with AsyncSessionLocal() as session:
            record = DebugResult(
                pipeline_id=pipeline_id,
                status=result.get("status", "unknown"),
                result_json=json.dumps(result, default=str),
                total_duration_ms=result.get("total_duration_ms", 0),
                error_type=class_out.get("error_type"),
                severity=class_out.get("severity"),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record.id
    except Exception as e:
        log.warning("db.save_failed", error=str(e))
        return None


async def get_pipeline_history(pipeline_id: str) -> list[dict]:
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DebugResult)
                .where(DebugResult.pipeline_id == pipeline_id)
                .order_by(DebugResult.created_at.desc())
                .limit(20)
            )
            rows = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "status": r.status,
                    "error_type": r.error_type,
                    "severity": r.severity,
                    "total_duration_ms": r.total_duration_ms,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ]
    except Exception as e:
        log.warning("db.history_failed", error=str(e))
        return []


async def save_feedback(
    pipeline_id: str,
    session_id: Optional[str],
    username: str,
    classification_correct: Optional[bool],
    fix_useful: Optional[bool],
    actual_error_type: Optional[str],
    comment: Optional[str],
) -> int:
    async with AsyncSessionLocal() as session:
        entry = FeedbackEntry(
            pipeline_id=pipeline_id,
            session_id=session_id,
            username=username,
            classification_correct=classification_correct,
            fix_useful=fix_useful,
            actual_error_type=actual_error_type,
            comment=comment,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry.id


async def get_feedback_metrics() -> dict:
    try:
        async with AsyncSessionLocal() as session:
            total_q = await session.execute(select(func.count(FeedbackEntry.id)))
            total = total_q.scalar() or 0

            class_q = await session.execute(
                select(
                    func.count(FeedbackEntry.id),
                    func.sum(case((FeedbackEntry.classification_correct == True, 1), else_=0)),
                ).where(FeedbackEntry.classification_correct.isnot(None))
            )
            class_row = class_q.one()
            class_total, class_correct = class_row
            class_acc = round((class_correct or 0) / class_total * 100, 1) if class_total else None

            fix_q = await session.execute(
                select(
                    func.count(FeedbackEntry.id),
                    func.sum(case((FeedbackEntry.fix_useful == True, 1), else_=0)),
                ).where(FeedbackEntry.fix_useful.isnot(None))
            )
            fix_row = fix_q.one()
            fix_total, fix_useful_count = fix_row
            fix_pct = round((fix_useful_count or 0) / fix_total * 100, 1) if fix_total else None

            breakdown_q = await session.execute(
                select(FeedbackEntry.actual_error_type, func.count(FeedbackEntry.id))
                .where(FeedbackEntry.actual_error_type.isnot(None))
                .group_by(FeedbackEntry.actual_error_type)
            )
            breakdown = {row[0]: row[1] for row in breakdown_q.all()}

            return {
                "total_feedback": total,
                "classification_accuracy_pct": class_acc,
                "fix_usefulness_pct": fix_pct,
                "breakdown_by_error_type": breakdown,
                "last_updated": datetime.now(timezone.utc),
            }
    except Exception as e:
        log.warning("db.metrics_failed", error=str(e))
        return {
            "total_feedback": 0,
            "classification_accuracy_pct": None,
            "fix_usefulness_pct": None,
            "breakdown_by_error_type": {},
            "last_updated": datetime.now(timezone.utc),
        }


async def get_all_feedback(limit: int = 50) -> list[dict]:
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(FeedbackEntry)
                .order_by(FeedbackEntry.created_at.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "pipeline_id": r.pipeline_id,
                    "username": r.username,
                    "classification_correct": r.classification_correct,
                    "fix_useful": r.fix_useful,
                    "actual_error_type": r.actual_error_type,
                    "comment": r.comment,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ]
    except Exception as e:
        log.warning("db.all_feedback_failed", error=str(e))
        return []


