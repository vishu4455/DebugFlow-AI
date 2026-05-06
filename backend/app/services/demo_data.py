"""
Mock mode middleware — returns realistic fake agent outputs when
DEMO_MODE=true is set in environment. Useful for UI development
and demos without a Gemini API key.
"""
import json
import random
from datetime import datetime, timedelta


DEMO_CLASSIFICATIONS = [
    {
        "error_type": "schema_mismatch",
        "severity": "high",
        "confidence": 91,
        "root_cause": "Column 'user_id' was renamed to 'uid' in the upstream CRM sync table, breaking the transformation schema contract.",
        "indicators": ["AnalysisException", "Cannot resolve attribute", "user_id", "schema mismatch", "stage failure"],
        "secondary_errors": ["shuffle_failure"],
        "affected_layer": "transform",
    },
    {
        "error_type": "oom",
        "severity": "critical",
        "confidence": 96,
        "root_cause": "Executor ran out of heap memory during shuffle phase due to high-cardinality groupBy on 312M rows with insufficient partition count.",
        "indicators": ["OutOfMemoryError", "GC overhead limit exceeded", "executor died", "TaskSetManager"],
        "secondary_errors": [],
        "affected_layer": "transform",
    },
    {
        "error_type": "missing_dependency",
        "severity": "high",
        "confidence": 98,
        "root_cause": "The staging schema was dropped during a database migration. dbt model finance_mart depends on staging.stg_transactions which no longer exists.",
        "indicators": ["relation does not exist", "staging.stg_transactions", "schema staging"],
        "secondary_errors": ["config_error"],
        "affected_layer": "load",
    },
    {
        "error_type": "auth_failure",
        "severity": "high",
        "confidence": 99,
        "root_cause": "Kafka consumer SASL credentials expired. The service account password was rotated but the consumer config was not updated.",
        "indicators": ["AuthorizationException", "SASL/PLAIN authentication failed", "Invalid credentials"],
        "secondary_errors": [],
        "affected_layer": "ingestion",
    },
]

DEMO_DEPENDENCIES = [
    {
        "upstream": [
            {"name": "crm_sync_v2", "type": "table", "status": "degraded", "impact": "high"},
            {"name": "payment_events_kafka", "type": "kafka", "status": "healthy", "impact": "medium"},
            {"name": "s3://datalake/sales/raw", "type": "s3", "status": "healthy", "impact": "high"},
        ],
        "downstream": [
            {"name": "finance_mart", "type": "table", "status": "blocked", "impact": "high"},
            {"name": "exec_dashboard", "type": "dashboard", "status": "stale", "impact": "high"},
            {"name": "revenue_forecast_ml", "type": "ml_model", "status": "degraded", "impact": "medium"},
            {"name": "weekly_board_report", "type": "report", "status": "blocked", "impact": "high"},
        ],
        "risk": "high",
        "blast_radius_summary": "Finance reporting, executive dashboards, and ML forecasting all blocked until pipeline recovers.",
        "slas_at_risk": ["Daily Revenue Report (08:00 UTC)", "CFO Dashboard SLA", "Weekly Board Pack"],
        "isolation_point": "etl_sales_daily output partition — downstream reads can be held at this boundary",
        "cascading_risk": "high",
    },
    {
        "upstream": [
            {"name": "clickstream_raw (kafka)", "type": "kafka", "status": "healthy", "impact": "high"},
            {"name": "user_profiles_pg", "type": "table", "status": "healthy", "impact": "medium"},
        ],
        "downstream": [
            {"name": "user_sessions_table", "type": "table", "status": "blocked", "impact": "high"},
            {"name": "recommendation_engine", "type": "ml_model", "status": "degraded", "impact": "medium"},
            {"name": "personalization_api", "type": "api", "status": "degraded", "impact": "medium"},
        ],
        "risk": "high",
        "blast_radius_summary": "Recommendation engine and personalization API running on stale data while Spark job is down.",
        "slas_at_risk": ["Realtime Personalization SLA", "Session Attribution Report"],
        "isolation_point": "Kafka consumer offset — can replay from last committed offset after fix",
        "cascading_risk": "medium",
    },
]

DEMO_FIXES = [
    {
        "title": "Schema Contract Restore: Column Alias + Contract Test",
        "steps": [
            {
                "step_num": 1,
                "action": "Add backward-compatible alias in the upstream CRM sync transformation",
                "code_hint": "SELECT uid AS user_id, session_id, event_ts AS ts, amount AS revenue FROM crm_raw",
                "estimated_time": "5 min",
            },
            {
                "step_num": 2,
                "action": "Run schema validation against target schema before reprocessing",
                "code_hint": "dbt test --select crm_sync --store-failures",
                "estimated_time": "3 min",
            },
            {
                "step_num": 3,
                "action": "Reprocess today's failed partition with fixed transformation",
                "code_hint": "airflow dags trigger etl_sales_daily --conf '{\"date\": \"2025-04-29\"}'",
                "estimated_time": "20 min",
            },
            {
                "step_num": 4,
                "action": "Verify downstream finance_mart row counts match expected range",
                "code_hint": "SELECT COUNT(*) FROM finance_mart WHERE dt = CURRENT_DATE;",
                "estimated_time": "5 min",
            },
            {
                "step_num": 5,
                "action": "Add schema contract test to CI/CD pipeline to catch future renames",
                "code_hint": "# dbt schema.yml\ncolumns:\n  - name: user_id\n    tests:\n      - not_null\n      - unique",
                "estimated_time": "30 min",
            },
        ],
        "estimated_time": "~63 min total",
        "validation_checks": [
            {"check": "Column alias produces correct user_id values", "result": "pass", "note": "Verified via row count match"},
            {"check": "Target schema contract satisfied", "result": "pass", "note": "dbt tests green"},
            {"check": "Downstream finance_mart rowcount within 5% of yesterday", "result": "warn", "note": "Reprocessing in progress"},
            {"check": "Airflow DAG marked success", "result": "pass", "note": None},
            {"check": "No new schema drift alerts in monitoring", "result": "pass", "note": None},
        ],
        "rollback_plan": "If reprocessed data fails validation, restore the previous finance_mart partition from the nightly snapshot at s3://datalake/snapshots/finance_mart/2025-04-28.",
        "preventive_measures": [
            "Implement schema registry (e.g. Confluent or AWS Glue) for all upstream tables",
            "Add dbt schema contract tests in CI that block upstream deployments on breaking changes",
            "Set up column-level lineage tracking in DataHub or OpenMetadata",
            "Create a Slack alert when any upstream schema changes are detected",
        ],
    },
    {
        "title": "OOM Fix: Increase Partitions + Driver Memory",
        "steps": [
            {
                "step_num": 1,
                "action": "Increase Spark partition count to reduce per-partition memory pressure",
                "code_hint": "spark.conf.set('spark.sql.shuffle.partitions', '800')\ndf = df.repartition(800, 'user_id')",
                "estimated_time": "5 min",
            },
            {
                "step_num": 2,
                "action": "Raise executor memory and enable off-heap storage",
                "code_hint": "--executor-memory 12g\n--conf spark.memory.offHeap.enabled=true\n--conf spark.memory.offHeap.size=4g",
                "estimated_time": "5 min",
            },
            {
                "step_num": 3,
                "action": "Add salting to high-cardinality join key to avoid shuffle skew",
                "code_hint": "df = df.withColumn('salt', (rand() * 10).cast('int'))\ndf = df.withColumn('user_id_salted', concat('user_id', lit('_'), col('salt')))",
                "estimated_time": "20 min",
            },
            {
                "step_num": 4,
                "action": "Re-run job with updated config and monitor Spark UI for stragglers",
                "code_hint": "spark-submit --master yarn --deploy-mode cluster ...",
                "estimated_time": "30 min",
            },
        ],
        "estimated_time": "~60 min total",
        "validation_checks": [
            {"check": "No OOM errors in executor logs", "result": "pass", "note": "Monitored via Spark UI"},
            {"check": "Stage completion time < 45 min (P95)", "result": "warn", "note": "Borderline — re-evaluate partitioning"},
            {"check": "Output row count matches Kafka lag clearing", "result": "pass", "note": None},
            {"check": "Memory utilization < 80% at peak", "result": "pass", "note": None},
        ],
        "rollback_plan": "Revert spark-submit config to previous values and reduce input batch size by filtering to the last 6 hours instead of 24.",
        "preventive_measures": [
            "Add adaptive query execution (AQE) — set spark.sql.adaptive.enabled=true",
            "Set memory watermark alerts at 75% in Grafana/Datadog",
            "Implement incremental micro-batch processing instead of daily full scans",
            "Add automatic partition skew detection in the pipeline pre-check step",
        ],
    },
]


def build_demo_metadata(pipeline_id: str) -> dict:
    now = datetime.utcnow()
    history = []
    for i in range(5):
        ts = now - timedelta(days=i)
        status = "failed" if i == 0 else ("success" if i % 3 != 2 else "failed")
        history.append({
            "run_id": f"run_{1000 - i}",
            "status": status,
            "timestamp": ts.isoformat() + "Z",
            "duration_min": round(random.uniform(12, 25), 1) if status == "success" else round(random.uniform(3, 8), 1),
            "rows_processed": random.randint(800000, 2000000) if status == "success" else 0,
        })
    return {
        "pipeline_id": pipeline_id,
        "environment": "prod",
        "last_successful_run": (now - timedelta(days=1)).isoformat() + "Z",
        "fail_count_7d": random.randint(2, 5),
        "avg_runtime_min": round(random.uniform(15, 22), 1),
        "data_volume": f"{round(random.uniform(1.5, 4.2), 1)}GB",
        "schedule": "daily 03:00 UTC",
        "owner": "data-platform-team",
        "tags": ["etl", "critical", "finance", "spark"],
        "run_history": history,
    }


def get_demo_output(agent: str, pipeline_id: str, idx: int = 0) -> dict:
    if agent == "metadata":
        return build_demo_metadata(pipeline_id)
    elif agent == "classification":
        return DEMO_CLASSIFICATIONS[idx % len(DEMO_CLASSIFICATIONS)]
    elif agent == "dependency":
        return DEMO_DEPENDENCIES[idx % len(DEMO_DEPENDENCIES)]
    elif agent == "fix":
        return DEMO_FIXES[idx % len(DEMO_FIXES)]
    elif agent == "log_fetch":
        return {"logs": "", "source": "inline", "status": "passthrough"}
    return {}
