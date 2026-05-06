import asyncio
import structlog
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

log = structlog.get_logger()


def _get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION,
    )


async def fetch_s3_logs(pipeline_id: str, max_bytes: int = 50_000) -> str:
    """
    Fetch the most recent log file for a pipeline from S3.
    Expects keys like: logs/{pipeline_id}/latest.log or logs/{pipeline_id}/YYYY-MM-DD.log
    """
    def _fetch():
        s3 = _get_s3_client()
        bucket = settings.S3_LOG_BUCKET
        prefix = f"logs/{pipeline_id}/"

        # List objects under pipeline prefix
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objects = resp.get("Contents", [])
        if not objects:
            raise FileNotFoundError(f"No log files found at s3://{bucket}/{prefix}")

        # Sort by LastModified descending → get latest
        latest = sorted(objects, key=lambda o: o["LastModified"], reverse=True)[0]
        key = latest["Key"]

        log.info("s3.fetching", bucket=bucket, key=key)
        obj = s3.get_object(Bucket=bucket, Key=key, Range=f"bytes=0-{max_bytes}")
        content = obj["Body"].read().decode("utf-8", errors="replace")
        return content

    return await asyncio.to_thread(_fetch)


async def list_s3_log_files(pipeline_id: str) -> list[dict]:
    """List all log files for a pipeline."""
    def _list():
        s3 = _get_s3_client()
        resp = s3.list_objects_v2(
            Bucket=settings.S3_LOG_BUCKET,
            Prefix=f"logs/{pipeline_id}/",
        )
        return [
            {
                "key": o["Key"],
                "size_kb": round(o["Size"] / 1024, 1),
                "last_modified": o["LastModified"].isoformat(),
            }
            for o in resp.get("Contents", [])
        ]

    return await asyncio.to_thread(_list)
