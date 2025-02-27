from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from script import process_videos, clean_to_delete

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "youtube_upload_cleanup",
    default_args=default_args,
    schedule_interval="0 3 * * *",
    catchup=False,
)

upload_task = PythonOperator(
    task_id="upload_videos",
    python_callable=process_videos,
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id="cleanup_files",
    python_callable=clean_to_delete,
    dag=dag,
)

upload_task >> cleanup_task