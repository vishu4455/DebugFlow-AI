"""
routers/stream.py — Server-Sent Events endpoint that streams agent results
as each agent completes, pushing { step, status, data } JSON events.
"""
from __future__ import annotations

import asyncio
import json
import time
import structlog

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.agents.log_fetch_agent import LogFetchAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.classifier_agent import ClassifierAgent
from app.agents.dependency_agent import DependencyAgent
from app.agents.fix_agent import FixAgent
from app.schemas.models import DebugRequest

log = structlog.get_logger()
router = APIRouter(tags=["Streaming"])


def sse_event(step: str, status: str, data: dict, duration_ms: float = 0) -> str:
    payload = json.dumps(
        {"step": step, "status": status, "data": data, "duration_ms": duration_ms},
        default=str,
    )
    return f"data: {payload}\n\n"


def sse_heartbeat() -> str:
    return ": heartbeat\n\n"


async def run_pipeline_stream(request: DebugRequest):
    """
    Async generator that yields SSE events as each agent finishes.
    Order: log_fetch → metadata+classification (parallel) → dependency → fix
    """
    log_fetcher        = LogFetchAgent()
    metadata_agent     = MetadataAgent()
    classifier_agent   = ClassifierAgent()
    dependency_agent   = DependencyAgent()
    fix_agent          = FixAgent()

    pipeline_id = request.pipeline_id

    # ── STARTED ──────────────────────────────────────────────────────────────
    yield sse_event("pipeline", "started", {"pipeline_id": pipeline_id})
    await asyncio.sleep(0)

    # ── STEP 1: Log Fetch ─────────────────────────────────────────────────────
    yield sse_event("log_fetch", "running", {})
    t = time.time()
    try:
        log_result = await log_fetcher.run(pipeline_id=pipeline_id, source=request.log_source)
        raw_logs = log_result.get("logs") or request.error_logs
        yield sse_event("log_fetch", "success", log_result, round((time.time() - t) * 1000, 1))
    except Exception as exc:
        raw_logs = request.error_logs
        yield sse_event("log_fetch", "error", {"error": str(exc)}, round((time.time() - t) * 1000, 1))
    await asyncio.sleep(0)

    # ── STEP 2a+2b: Metadata + Classification (parallel) ─────────────────────
    yield sse_event("metadata", "running", {})
    yield sse_event("classification", "running", {})

    meta_result = class_result = None

    async def _run_metadata():
        nonlocal meta_result
        t2 = time.time()
        try:
            meta_result = await metadata_agent.run(
                pipeline_id=pipeline_id, config=request.pipeline_config
            )
        except Exception as exc:
            meta_result = {"error": str(exc)}

    async def _run_classification():
        nonlocal class_result
        t2 = time.time()
        try:
            class_result = await classifier_agent.run(logs=raw_logs, pipeline_id=pipeline_id)
        except Exception as exc:
            class_result = {"error": str(exc)}

    t2 = time.time()
    await asyncio.gather(_run_metadata(), _run_classification())
    parallel_ms = round((time.time() - t2) * 1000, 1)

    has_meta_error = "error" in (meta_result or {})
    has_class_error = "error" in (class_result or {})

    yield sse_event(
        "metadata",
        "error" if has_meta_error else "success",
        meta_result or {},
        parallel_ms,
    )
    yield sse_event(
        "classification",
        "error" if has_class_error else "success",
        class_result or {},
        parallel_ms,
    )
    await asyncio.sleep(0)

    # ── STEP 3: Dependency ────────────────────────────────────────────────────
    yield sse_event("dependency", "running", {})
    t3 = time.time()
    try:
        dep_result = await dependency_agent.run(
            pipeline_id=pipeline_id,
            classification=class_result or {},
            config=request.pipeline_config,
        )
        yield sse_event("dependency", "success", dep_result, round((time.time() - t3) * 1000, 1))
    except Exception as exc:
        dep_result = {"error": str(exc)}
        yield sse_event("dependency", "error", dep_result, round((time.time() - t3) * 1000, 1))
    await asyncio.sleep(0)

    # ── STEP 4: Fix ───────────────────────────────────────────────────────────
    yield sse_event("fix", "running", {})
    t4 = time.time()
    try:
        fix_result = await fix_agent.run(
            logs=raw_logs,
            classification=class_result or {},
            dependency=dep_result,
            pipeline_id=pipeline_id,
        )
        yield sse_event("fix", "success", fix_result, round((time.time() - t4) * 1000, 1))
    except Exception as exc:
        fix_result = {"error": str(exc)}
        yield sse_event("fix", "error", fix_result, round((time.time() - t4) * 1000, 1))
    await asyncio.sleep(0)

    # ── DONE ─────────────────────────────────────────────────────────────────
    yield sse_event("pipeline", "complete", {"pipeline_id": pipeline_id})


@router.post("/stream/debug")
async def stream_debug(
    payload: DebugRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    SSE endpoint — POST the debug request, receive a stream of agent events.

    Each event:  data: {"step": "...", "status": "running|success|error", "data": {...}, "duration_ms": 0}\n\n
    Final event: data: {"step": "pipeline", "status": "complete", ...}\n\n
    """
    log.info("stream_debug.start", pipeline_id=payload.pipeline_id, user=current_user.get("username"))

    async def event_stream():
        try:
            async for chunk in run_pipeline_stream(payload):
                # Check if client disconnected
                if await request.is_disconnected():
                    log.info("stream_debug.client_disconnected")
                    break
                yield chunk
        except asyncio.CancelledError:
            log.info("stream_debug.cancelled")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":       "no-cache",
            "X-Accel-Buffering":   "no",      # disable nginx buffering
            "Connection":          "keep-alive",
        },
    )
