from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def fail_task():
    raise ValueError("Schema mismatch: column 'user_id' not found in source table. Expected schema: [user_id, session_id, ts, revenue] but got: [uid, session_id, event_ts, amount]")

with DAG(
    dag_id="failing_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
) as dag:
    PythonOperator(
        task_id="extract_users",
        python_callable=fail_task,
    )