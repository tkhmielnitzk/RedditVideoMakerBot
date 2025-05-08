from airflow import DAG
from airflow.operators.bash import BashOperator
# from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime
from datetime import timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 3, 31),
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

with DAG(
    "youtube_video_upload",
    default_args=default_args,
    description="DAG to trigger YouTube video upload",
    schedule_interval=timedelta(days=1),
    catchup=False,
    max_active_runs=1,
    concurrency=1
    ) as dag:

    create_video = BashOperator(
        task_id="create_video",
        # bash_command="docker exec youtube-uploader python /app/manage_videos.py",
        bash_command="docker exec my_bot python /app/main.py",
        dag=dag,
    )

    upload_video = BashOperator(
        task_id="upload_video",
        # bash_command="docker exec my-bot python /app/main.py",
        bash_command="docker exec youtube-uploader python /app/manage_videos.py",
        dag=dag,
    )

    # upload_video = DockerOperator(
    #     task_id="upload_video",
    #     image="youtube-uploader",
    #     api_version="auto",
    #     auto_remove='never',
    #     command="python /app/manage_videos.py",
    #     network_mode="bridge",
    #     dag=dag,
    # )

    create_video >> upload_video
    # upload_video
    # create_video

    