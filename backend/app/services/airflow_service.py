"""
services/airflow_service.py

Complete Airflow REST API integration with:
- Connection health check
- List all DAGs
- List DAG runs with state filter
- List task instances for a run
- Fetch task logs (with full diagnostics on failure)
- Detailed error messages so the UI can show exactly what went wrong
"""
import re
import httpx
import structlog
from typing import Optional
from app.core.config import settings

log = structlog.get_logger()


def _client(timeout: int = 20) -> httpx.AsyncClient:
    """Return a configured httpx client with Basic auth."""
    return httpx.AsyncClient(
        base_url=settings.AIRFLOW_BASE_URL,
        auth=(settings.AIRFLOW_USERNAME, settings.AIRFLOW_PASSWORD),
        timeout=timeout,
        headers={"Content-Type": "application/json"},
        # Don't verify SSL in dev — set to True or a cert path in prod
        verify=False,
    )


# ─── Connection test ─────────────────────────────────────────────────────────

async def test_connection() -> dict:
    """
    Test whether the Airflow API is reachable and credentials are valid.
    Returns { ok, version, message }.
    """
    try:
        async with _client(timeout=8) as client:
            resp = await client.get("/api/v1/version")
            if resp.status_code == 401:
                return {
                    "ok": False,
                    "message": "Authentication failed — check AIRFLOW_USERNAME and AIRFLOW_PASSWORD",
                    "status_code": 401,
                }
            if resp.status_code == 404:
                return {
                    "ok": False,
                    "message": "Airflow REST API not found — make sure api_auth_backends is enabled in airflow.cfg",
                    "status_code": 404,
                }
            resp.raise_for_status()
            data = resp.json()
            return {
                "ok": True,
                "version": data.get("version", "unknown"),
                "git_version": data.get("git_version", ""),
                "message": f"Connected to Airflow {data.get('version', '')}",
                "base_url": settings.AIRFLOW_BASE_URL,
            }
    except httpx.ConnectError:
        return {
            "ok": False,
            "message": f"Cannot connect to {settings.AIRFLOW_BASE_URL} — is Airflow running?",
        }
    except httpx.TimeoutException:
        return {
            "ok": False,
            "message": f"Connection timed out to {settings.AIRFLOW_BASE_URL}",
        }
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


# ─── List DAGs ───────────────────────────────────────────────────────────────

async def list_dags(only_active: bool = True) -> list[dict]:
    """Return a list of all DAGs with key metadata."""
    async with _client() as client:
        resp = await client.get(
            "/api/v1/dags",
            params={"limit": 100, "only_active": str(only_active).lower()},
        )
        _raise_with_detail(resp)
        dags = resp.json().get("dags", [])
        return [
            {
                "dag_id":       d.get("dag_id"),
                "description":  d.get("description", ""),
                "is_paused":    d.get("is_paused", False),
                "is_active":    d.get("is_active", True),
                "owners":       d.get("owners", []),
                "tags":         [t.get("name") for t in d.get("tags", [])],
                "schedule":     d.get("schedule_interval", {}).get("value") if isinstance(d.get("schedule_interval"), dict) else d.get("schedule_interval"),
                "last_parsed":  d.get("last_parsed_time"),
                "file_token":   d.get("file_token"),
            }
            for d in dags
        ]


# ─── List DAG runs ───────────────────────────────────────────────────────────

async def list_dag_runs(dag_id: str, limit: int = 10, state: Optional[str] = None) -> list[dict]:
    """
    List recent runs for a DAG.
    state: 'failed' | 'success' | 'running' | None (all)
    """
    params = {"order_by": "-execution_date", "limit": limit}
    if state:
        params["state"] = state

    async with _client() as client:
        resp = await client.get(f"/api/v1/dags/{dag_id}/dagRuns", params=params)
        _raise_with_detail(resp)
        runs = resp.json().get("dag_runs", [])
        return [
            {
                "dag_run_id":     r.get("dag_run_id"),
                "state":          r.get("state"),
                "execution_date": r.get("execution_date"),
                "start_date":     r.get("start_date"),
                "end_date":       r.get("end_date"),
                "run_type":       r.get("run_type"),
                "conf":           r.get("conf", {}),
                "duration_sec":   _calc_duration(r.get("start_date"), r.get("end_date")),
            }
            for r in runs
        ]


# ─── List task instances ──────────────────────────────────────────────────────

async def list_task_instances(dag_id: str, run_id: str) -> list[dict]:
    """List all task instances for a specific DAG run."""
    async with _client() as client:
        resp = await client.get(
            f"/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances"
        )
        _raise_with_detail(resp)
        tasks = resp.json().get("task_instances", [])
        return [
            {
                "task_id":        t.get("task_id"),
                "state":          t.get("state"),
                "try_number":     t.get("try_number", 1),
                "max_tries":      t.get("max_tries", 0),
                "start_date":     t.get("start_date"),
                "end_date":       t.get("end_date"),
                "duration":       t.get("duration"),
                "operator":       t.get("operator"),
                "priority":       t.get("priority_weight"),
                "log_url":        t.get("log_url"),
            }
            for t in tasks
        ]


# ─── Fetch task logs ─────────────────────────────────────────────────────────

async def fetch_task_logs(
    dag_id: str,
    run_id: str,
    task_id: str,
    try_number: int = 1,
    full_content: bool = True,
) -> dict:
    """
    Fetch logs for a specific task instance.
    Returns { logs, source_url, warnings }.
    Raises AirflowFetchError with a clear message on failure.
    """
    url = f"/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs/{try_number}"

    async with _client(timeout=30) as client:
        resp = await client.get(url, params={"full_content": str(full_content).lower()})

        if resp.status_code == 404:
            raise AirflowFetchError(
                f"Logs not found for task '{task_id}' (try #{try_number}).\n"
                f"The task may not have run yet, or logs may have been cleared.\n"
                f"URL tried: {settings.AIRFLOW_BASE_URL}{url}"
            )
        if resp.status_code == 403:
            raise AirflowFetchError(
                f"Permission denied fetching logs for '{task_id}'.\n"
                f"Check that user '{settings.AIRFLOW_USERNAME}' has the 'Op' or 'Admin' role."
            )

        _raise_with_detail(resp)

        raw = resp.text

        # Airflow sometimes wraps logs in JSON { "content": "...", "continuation_token": "..." }
        logs = raw
        warnings = []
        try:
            import json
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                logs = parsed.get("content", raw)
                if parsed.get("continuation_token"):
                    warnings.append("Log was truncated — there are more entries. Increase log_fetch_timeout in airflow.cfg to get full logs.")
        except Exception:
            pass  # plain text response — use as-is

        if not logs.strip():
            warnings.append("Log content is empty. The task may have failed before writing any logs.")

        log.info(
            "airflow.logs_fetched",
            dag_id=dag_id, run_id=run_id, task_id=task_id,
            try_number=try_number, log_bytes=len(logs),
        )
        return {
            "logs":       logs,
            "source_url": f"{settings.AIRFLOW_BASE_URL}{url}",
            "warnings":   warnings,
            "task_id":    task_id,
            "run_id":     run_id,
            "try_number": try_number,
        }


# ─── High-level: fetch latest failure logs ───────────────────────────────────

async def fetch_airflow_logs(pipeline_id: str) -> str:
    """
    Convenience: find the latest failed run → failed task → fetch logs.
    Returns raw log string. Raises AirflowFetchError with a clear message.
    """
    # Step 1: get recent runs
    log.info("airflow.fetch_start", dag_id=pipeline_id)
    runs = await list_dag_runs(pipeline_id, limit=10)

    if not runs:
        raise AirflowFetchError(
            f"DAG '{pipeline_id}' has no runs yet.\n"
            f"Trigger the DAG in Airflow first, or check the DAG ID is correct.\n"
            f"Available at: {settings.AIRFLOW_BASE_URL}/dags"
        )

    # Step 2: pick most recent failed run (fallback to latest)
    failed_run = next((r for r in runs if r["state"] == "failed"), None)
    if not failed_run:
        states = [r["state"] for r in runs]
        raise AirflowFetchError(
            f"No failed runs found for DAG '{pipeline_id}'.\n"
            f"Recent run states: {states}\n"
            f"If the DAG is still running, wait for it to finish."
        )

    run_id = failed_run["dag_run_id"]
    log.info("airflow.found_failed_run", dag_id=pipeline_id, run_id=run_id)

    # Step 3: find failed task instance
    tasks = await list_task_instances(pipeline_id, run_id)
    if not tasks:
        raise AirflowFetchError(
            f"Run '{run_id}' has no task instances.\n"
            f"This may be a sensor or empty DAG."
        )

    failed_task = next((t for t in tasks if t["state"] == "failed"), None)
    if not failed_task:
        task_states = [(t["task_id"], t["state"]) for t in tasks]
        raise AirflowFetchError(
            f"No failed tasks in run '{run_id}'.\n"
            f"Task states: {task_states}"
        )

    # Step 4: fetch logs
    result = await fetch_task_logs(
        dag_id=pipeline_id,
        run_id=run_id,
        task_id=failed_task["task_id"],
        try_number=failed_task.get("try_number", 1),
    )
    return result["logs"]


# ─── Helpers ─────────────────────────────────────────────────────────────────

class AirflowFetchError(Exception):
    """Raised when Airflow log fetching fails with a user-readable message."""
    pass


def _raise_with_detail(resp: httpx.Response):
    """Raise an AirflowFetchError with a detailed message for non-2xx responses."""
    if resp.is_success:
        return
    try:
        detail = resp.json().get("detail", resp.text[:300])
    except Exception:
        detail = resp.text[:300]
    raise AirflowFetchError(
        f"Airflow API returned HTTP {resp.status_code}: {detail}\n"
        f"URL: {resp.url}"
    )


def _calc_duration(start: Optional[str], end: Optional[str]) -> Optional[float]:
    """Return duration in seconds between two ISO timestamps."""
    if not start or not end:
        return None
    try:
        from datetime import datetime, timezone
        fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
        s = datetime.fromisoformat(start.replace("Z", "+00:00"))
        e = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return round((e - s).total_seconds(), 1)
    except Exception:
        return None
