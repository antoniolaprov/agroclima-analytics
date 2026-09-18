import pytest

# Usa "airflow.models" (nao apenas "airflow") no importorskip porque o
# projeto tem seu proprio diretorio de nivel superior "airflow/" (para os
# DAGs). Sem o pacote airflow instalado, esse diretorio e' resolvido pelo
# Python como um namespace package chamado "airflow", entao
# importorskip("airflow") teria sucesso e o teste falharia ao tentar
# "from airflow.models import DagBag" em vez de pular.
pytest.importorskip("airflow.models")

from airflow.models import DagBag


def test_dag_carrega_sem_erro():
    bag = DagBag(dag_folder="airflow/dags", include_examples=False)
    assert bag.import_errors == {}
    assert "agroclima_pipeline" in bag.dags


def test_dag_tem_as_tarefas_esperadas():
    bag = DagBag(dag_folder="airflow/dags", include_examples=False)
    tarefas = set(bag.dags["agroclima_pipeline"].task_ids)
    assert tarefas == {
        "start", "ingest_inmet_estacoes", "ingest_inmet_clima",
        "ingest_sidra", "dbt_build", "notify", "end",
    }


def test_ingestoes_rodam_em_paralelo_antes_do_dbt():
    dag = DagBag(dag_folder="airflow/dags", include_examples=False).dags["agroclima_pipeline"]
    assert dag.get_task("dbt_build").upstream_task_ids == {
        "ingest_inmet_estacoes", "ingest_inmet_clima", "ingest_sidra",
    }
