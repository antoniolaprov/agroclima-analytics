from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

from src import config
from src.ingestion import inmet_api, sidra_api
from src.pipeline import rodar_dbt

default_args = {
    "owner": "antoniolaprov",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _clima():
    return inmet_api.ingest_clima(config.ANOS_CLIMA)


def _notificar(**contexto):
    ti = contexto["ti"]
    print("estacoes:", ti.xcom_pull(task_ids="ingest_inmet_estacoes"))
    print("clima:", ti.xcom_pull(task_ids="ingest_inmet_clima"))
    print("sidra:", ti.xcom_pull(task_ids="ingest_sidra"))


with DAG(
    dag_id="agroclima_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="0 9 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["agroclima"],
) as dag:
    start = EmptyOperator(task_id="start")

    estacoes = PythonOperator(
        task_id="ingest_inmet_estacoes",
        python_callable=inmet_api.ingest_estacoes,
    )
    clima = PythonOperator(task_id="ingest_inmet_clima", python_callable=_clima)
    sidra = PythonOperator(
        task_id="ingest_sidra",
        python_callable=lambda: {"pam": sidra_api.ingest_pam(), "lspa": sidra_api.ingest_lspa()},
    )

    dbt = PythonOperator(task_id="dbt_build", python_callable=rodar_dbt)
    notify = PythonOperator(task_id="notify", python_callable=_notificar)
    end = EmptyOperator(task_id="end")

    start >> [estacoes, clima, sidra] >> dbt >> notify >> end
