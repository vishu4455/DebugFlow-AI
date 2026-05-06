import time
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator

from app.services.db import init_db, get_pipeline_history
from app.services.cache import init_redis, close_redis
from app.schemas.models import DebugRequest, DebugResponse, PipelineStatusResponse, HealthResponse
from app.orchestrator import Orchestrator
from app.auth.dependencies import get_current_user
from app.routers import auth as auth_router
from app.routers import stream as stream_router
from app.routers import feedback as feedback_router
from app.routers import airflow as airflow_router

log = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", msg="Initializing services")
    await init_db()
    await init_redis()
    yield
    log.info("shutdown", msg="Closing connections")
    await close_redis()


app = FastAPI(
    title="Pipeline Failure Debugger API",
    description="Agentic AI system for diagnosing and fixing data pipeline failures",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Instrumentator().instrument(app).expose(app)

app.include_router(auth_router.router)
app.include_router(stream_router.router)
app.include_router(feedback_router.router)
app.include_router(airflow_router.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    log.info("request", method=request.method, path=request.url.path,
             status=response.status_code, duration_ms=duration)
    return response


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return HealthResponse(status="ok", version="2.0.0")


@app.post("/debug-failure", response_model=DebugResponse, tags=["Debug"])
@limiter.limit("10/minute")
async def debug_failure(
    request: Request,
    payload: DebugRequest,
    current_user: dict = Depends(get_current_user),
):
    log.info("debug_failure.start", pipeline_id=payload.pipeline_id, user=current_user.get("username"))
    orchestrator = Orchestrator()
    try:
        result = await orchestrator.run(payload)
        return result
    except Exception as exc:
        log.error("debug_failure.error", error=str(exc))
        return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/pipeline-status", response_model=PipelineStatusResponse, tags=["Pipeline"])
@limiter.limit("30/minute")
async def pipeline_status(
    request: Request,
    pipeline_id: str,
    current_user: dict = Depends(get_current_user),
):
    history = await get_pipeline_history(pipeline_id)
    return PipelineStatusResponse(pipeline_id=pipeline_id, history=history)
