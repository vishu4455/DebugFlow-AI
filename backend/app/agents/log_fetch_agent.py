import structlog
from app.services.airflow_service import fetch_airflow_logs, AirflowFetchError
from app.services.s3_service import fetch_s3_logs

log = structlog.get_logger()


class LogFetchAgent:
    """
    Fetches raw pipeline logs from external sources.
    Returns a dict with logs + fetch metadata so the UI can show status.
    """

    async def run(self, pipeline_id: str, source: str | None = "inline") -> dict:
        log.info("log_fetch_agent.run", pipeline_id=pipeline_id, source=source)

        if source == "airflow":
            try:
                logs = await fetch_airflow_logs(pipeline_id)
                return {
                    "logs":   logs,
                    "source": "airflow",
                    "status": "fetched",
                    "bytes":  len(logs),
                }
            except AirflowFetchError as e:
                # AirflowFetchError has a user-readable message — surface it
                log.warning("log_fetch.airflow_failed", error=str(e))
                return {
                    "logs":     "",
                    "source":   "airflow",
                    "status":   "failed",
                    "error":    str(e),
                    "fallback": "Using inline logs from request body",
                }
            except Exception as e:
                log.warning("log_fetch.airflow_unexpected", error=str(e))
                return {
                    "logs":     "",
                    "source":   "airflow",
                    "status":   "failed",
                    "error":    f"Unexpected error: {str(e)}",
                    "fallback": "Using inline logs from request body",
                }

        elif source == "s3":
            try:
                logs = await fetch_s3_logs(pipeline_id)
                return {
                    "logs":   logs,
                    "source": "s3",
                    "status": "fetched",
                    "bytes":  len(logs),
                }
            except Exception as e:
                log.warning("log_fetch.s3_failed", error=str(e))
                return {
                    "logs":     "",
                    "source":   "s3",
                    "status":   "failed",
                    "error":    str(e),
                    "fallback": "Using inline logs from request body",
                }

        else:
            return {
                "logs":   "",
                "source": "inline",
                "status": "passthrough",
                "note":   "Using inline logs provided in request body",
            }
