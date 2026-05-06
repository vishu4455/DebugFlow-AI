"""
routers/airflow.py — Airflow integration endpoints for the web UI.

GET  /airflow/status          — test connection
GET  /airflow/dags            — list all DAGs
GET  /airflow/dags/{dag_id}/runs         — list runs for a DAG
GET  /airflow/dags/{dag_id}/runs/{run_id}/tasks  — list task instances
GET  /airflow/dags/{dag_id}/runs/{run_id}/tasks/{task_id}/logs  — fetch logs
POST /airflow/fetch-logs      — high-level: find + return latest failure logs
"""
from __future__ import annotations

from typing import Optional
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.services.airflow_service import (
    test_connection,
    list_dags,
    list_dag_runs,
    list_task_instances,
    fetch_task_logs,
    fetch_airflow_logs,
    AirflowFetchError,
)

log = structlog.get_logger()
router = APIRouter(prefix="/airflow", tags=["Airflow"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class FetchLogsRequest(BaseModel):
    dag_id: str
    run_id: Optional[str] = None    # if None → auto-pick latest failed run
    task_id: Optional[str] = None   # if None → auto-pick failed task
    try_number: int = 1


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/status")
async def airflow_status(_user: dict = Depends(get_current_user)):
    """Test Airflow connectivity and return version info."""
    return await test_connection()


@router.get("/dags")
async def get_dags(
    only_active: bool = True,
    _user: dict = Depends(get_current_user),
):
    """List all DAGs from Airflow."""
    try:
        return {"dags": await list_dags(only_active=only_active)}
    except AirflowFetchError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Airflow error: {str(e)}")


@router.get("/dags/{dag_id}/runs")
async def get_dag_runs(
    dag_id: str,
    limit: int = Query(10, ge=1, le=100),
    state: Optional[str] = Query(None, description="failed|success|running"),
    _user: dict = Depends(get_current_user),
):
    """List recent runs for a specific DAG."""
    try:
        runs = await list_dag_runs(dag_id, limit=limit, state=state)
        return {"dag_id": dag_id, "runs": runs, "count": len(runs)}
    except AirflowFetchError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Airflow error: {str(e)}")


@router.get("/dags/{dag_id}/runs/{run_id}/tasks")
async def get_task_instances(
    dag_id: str,
    run_id: str,
    _user: dict = Depends(get_current_user),
):
    """List all task instances for a DAG run."""
    try:
        tasks = await list_task_instances(dag_id, run_id)
        return {"dag_id": dag_id, "run_id": run_id, "tasks": tasks}
    except AirflowFetchError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/dags/{dag_id}/runs/{run_id}/tasks/{task_id}/logs")
async def get_task_logs(
    dag_id: str,
    run_id: str,
    task_id: str,
    try_number: int = Query(1, ge=1),
    _user: dict = Depends(get_current_user),
):
    """Fetch raw logs for a specific task instance."""
    try:
        result = await fetch_task_logs(dag_id, run_id, task_id, try_number)
        return result
    except AirflowFetchError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/fetch-logs")
async def fetch_logs_auto(
    body: FetchLogsRequest,
    _user: dict = Depends(get_current_user),
):
    """
    Smart log fetch: auto-detects latest failed run + task if not specified.
    Returns logs ready to paste into the debug pipeline.
    """
    try:
        if body.run_id and body.task_id:
            # Specific task specified
            result = await fetch_task_logs(
                body.dag_id, body.run_id, body.task_id, body.try_number
            )
            return {
                "success": True,
                "logs": result["logs"],
                "source_url": result["source_url"],
                "warnings": result["warnings"],
                "task_id": result["task_id"],
                "run_id": result["run_id"],
            }
        else:
            # Auto-detect latest failure
            logs = await fetch_airflow_logs(body.dag_id)
            return {
                "success": True,
                "logs": logs,
                "warnings": [],
            }
    except AirflowFetchError as e:
        log.warning("airflow.fetch_failed", dag_id=body.dag_id, error=str(e))
        return {
            "success": False,
            "logs": "",
            "error": str(e),
            "diagnosis": _diagnose_error(str(e)),
        }
    except Exception as e:
        return {
            "success": False,
            "logs": "",
            "error": str(e),
            "diagnosis": "Unexpected error — check backend logs for details.",
        }


def _diagnose_error(error_msg: str) -> str:
    """Return a human-readable fix suggestion based on the error message."""
    msg = error_msg.lower()
    if "cannot connect" in msg or "connection refused" in msg:
        return (
            "Airflow is not reachable. Check:\n"
            "1. AIRFLOW_BASE_URL in .env is correct\n"
            "2. Airflow webserver is running\n"
            "3. The port is open (default: 8080)"
        )
    if "401" in msg or "authentication" in msg:
        return (
            "Wrong credentials. Check:\n"
            "1. AIRFLOW_USERNAME in .env\n"
            "2. AIRFLOW_PASSWORD in .env\n"
            "3. User has 'Op' or 'Admin' role in Airflow"
        )
    if "404" in msg or "not found" in msg:
        return (
            "DAG or resource not found. Check:\n"
            "1. DAG ID matches exactly (case-sensitive)\n"
            "2. DAG has been uploaded to Airflow\n"
            "3. REST API is enabled in airflow.cfg"
        )
    if "403" in msg or "permission" in msg:
        return (
            "Permission denied. In Airflow UI:\n"
            "Security → List Users → Edit your user → Role: Op or Admin"
        )
    if "no runs" in msg or "no failed" in msg:
        return (
            "No failed runs found. Either:\n"
            "1. The DAG hasn't run yet — trigger it manually\n"
            "2. All recent runs succeeded\n"
            "3. Wrong DAG ID"
        )
    if "timed out" in msg:
        return (
            "Connection timed out. Check:\n"
            "1. AIRFLOW_BASE_URL is correct\n"
            "2. Network/firewall allows the connection\n"
            "3. Try increasing timeout in airflow_service.py"
        )
    return "Check AIRFLOW_BASE_URL, AIRFLOW_USERNAME, AIRFLOW_PASSWORD in backend/.env"
