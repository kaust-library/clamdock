from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

with DAG(
    dag_id="update_db_dag",
    description="Update AV database"
) as dag:
    update_db = DockerOperator(
        task_id="update_db",
        image="clamav/clamav",
        command=[
            "freshclam",
        ],
        mounts=[
            (source="clam_db", target="/var/lib/clamav"),
        ],
        network_mode="airflow",
    )