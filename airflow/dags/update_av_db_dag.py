import airflow
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

with DAG(
    dag_id="update_db_dag",
    description="Update AV database",
    start_date=airflow.utils.dates.days_ago(10),
    schedule_interval=None,
) as dag:
    update_db = DockerOperator(
        task_id="update_db",
        auto_remove=True,
        tty=True,
        container_name="fresh_clam_db",
        xcom_all=False,
        mount_tmp_dir=False,
        docker_url="unix://var/run/docker.sock",
        image="clamav/clamav:latest",
        command="freshclam"
        mounts=[
            ("/var/lib/clamav","clam_db")
        ],
    )