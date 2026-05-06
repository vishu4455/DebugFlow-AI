export const PIPELINE_PRESETS = {
  etl_sales: {
    id: "etl_sales_daily_v2",
    label: "etl_sales_daily",
    logs: `ERROR: AnalysisException: Resolved attribute(s) 'user_id' missing from child struct
  at com.databricks.sql.analyzer.Analyzer.failAnalysis(Analyzer.scala:892)
  Schema mismatch: expected [user_id, session_id, ts, revenue] got [uid, session_id, event_ts, amount]
  Task failed: stage 12 (ShuffleMapStage), attempt 3
  Job aborted due to stage failure.`,
    config: `Source: s3://datalake/sales/raw/2025-04-29/
Target: redshift.prod.sales_daily
Upstream: crm_sync, payment_events
Downstream: finance_mart, exec_dashboard, revenue_forecast
Spark 3.4, 16 executors, 8GB each
Schedule: daily 03:00 UTC`,
    source: "inline",
  },
  spark_oom: {
    id: "spark_clickstream_agg_prod",
    label: "spark_clickstream_agg",
    logs: `java.lang.OutOfMemoryError: GC overhead limit exceeded
  at org.apache.spark.sql.catalyst.expressions.codegen.BufferHolder.grow(BufferHolder.java:78)
  Driver memory: 4GB / 4GB used. 312M rows in shuffle.
  WARN TaskSetManager: Lost task 0.3 in stage 14.0 (executor died)
  ERROR SparkContext: Error initializing SparkContext.`,
    config: `Input: kafka topic clickstream_raw, lag=2.1M msgs
GroupBy: user_id, session_id, hour (high cardinality)
Executor: 4GB RAM, 8 cores
Downstream: user_sessions table, recommendation_engine`,
    source: "inline",
  },
  dbt_missing: {
    id: "dbt_finance_mart",
    label: "dbt_finance_mart",
    logs: `Database Error in model finance_mart (models/finance/finance_mart.sql)
  relation "staging.stg_transactions" does not exist
  compiled SQL at target/compiled/finance/finance_mart.sql
PSQL Error: ERROR: schema "staging" does not exist
  LINE 1: FROM staging.stg_transactions`,
    config: `dbt version: 1.7.3
Target: postgres prod
Depends on: stg_transactions, stg_accounts, stg_fx_rates
Scheduled: 06:00 UTC daily
Owner: data-finance-team`,
    source: "inline",
  },
  kafka_auth: {
    id: "kafka_events_consumer_v1",
    label: "kafka_events_consumer",
    logs: `org.apache.kafka.common.errors.AuthorizationException: Not authorized to access topics: [user_events_prod]
  Consumer group: analytics-consumer-group-v1
  Broker: kafka-prod-01:9092
  SASL/PLAIN authentication failed: Invalid credentials
  Caused by: javax.security.sasl.SaslException: Authentication failed`,
    config: `Consumer: analytics-consumer-group-v1
Topics: user_events_prod, page_views_prod
Sink: BigQuery analytics.events_raw
Downstream: ML feature pipeline, A/B test tracker`,
    source: "inline",
  },
  custom: { id: "", label: "Custom Pipeline", logs: "", config: "", source: "inline" },
};

export const AGENT_META = [
  { key: "log_fetch", icon: "📥", label: "Log Fetch", desc: "Airflow / S3 / Inline" },
  { key: "metadata", icon: "📋", label: "Metadata", desc: "Run history · Config" },
  { key: "classification", icon: "🔍", label: "Classifier", desc: "Schema · OOM · Auth" },
  { key: "dependency", icon: "🕸", label: "Dependencies", desc: "Blast radius · Graph" },
  { key: "fix", icon: "🔧", label: "Fix Generator", desc: "Remediation · Validation" },
];
