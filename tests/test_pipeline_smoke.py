"""Teste de fumaca ponta a ponta: gera uma Bronze pequena, roda o "dbt build"
de verdade contra ela (copia isolada do projeto dbt, DuckDB temporario) e
confere que as tabelas Gold saem populadas.

Reaproveita os mesmos geradores de scripts/seed_bronze_dev.py, ja desenhados
para satisfazer os testes singulares do dbt (lacuna de ano no PAM, estacao
excluida com historico valido, milho LSPA x PAM etc.), entao este teste
tambem cobre staging + marts + os testes dbt na ordem real do grafo - a
unica parte do pipeline que um teste unitario isolado nao alcanca.

Nao cobre a ingestao de rede (INMET/SIDRA) nem o Airflow; isso e' coberto
por tests/test_inmet_*.py, tests/test_sidra.py e tests/test_dag.py com
fixtures e mocks.
"""

import shutil

import duckdb

from scripts import seed_bronze_dev
from src import config, pipeline

DBT_REAL_DIR = config.RAIZ / "dbt"


def test_pipeline_smoke_dbt_build_popula_as_tabelas_gold(tmp_path, monkeypatch):
    projeto_dbt = tmp_path / "dbt"
    shutil.copytree(
        DBT_REAL_DIR,
        projeto_dbt,
        ignore=shutil.ignore_patterns("target", "logs", "__pycache__"),
    )

    bronze_dir = tmp_path / "data" / "bronze"
    monkeypatch.setattr(seed_bronze_dev.config, "BRONZE_DIR", bronze_dir)
    seed_bronze_dev.escrever(seed_bronze_dev.gerar_estacoes(), "estacoes")
    seed_bronze_dev.escrever(seed_bronze_dev.gerar_clima_horario(), "clima_horario", particao="2026")
    seed_bronze_dev.escrever(seed_bronze_dev.gerar_pam(), "pam")
    seed_bronze_dev.escrever(seed_bronze_dev.gerar_lspa(), "lspa")

    # profiles.yml e sources.yml do projeto copiado usam caminhos relativos
    # ("../data/...") resolvidos contra o cwd do processo dbt (ver
    # comentario em src/pipeline.rodar_dbt); por isso a Bronze fabricada e o
    # DuckDB temporario ficam em tmp_path/data, irmao de tmp_path/dbt.
    monkeypatch.setattr(pipeline, "DBT_DIR", projeto_dbt)
    pipeline.rodar_dbt()

    banco = tmp_path / "data" / "warehouse.duckdb"
    assert banco.exists(), "dbt build rodou mas nao criou o warehouse esperado"

    con = duckdb.connect(str(banco), read_only=True)
    try:
        for tabela in ("gold_safra_uf", "gold_clima_uf_mensal", "gold_clima_safra"):
            total = con.execute(f"select count(*) from {tabela}").fetchone()[0]
            assert total > 0, f"{tabela} saiu vazia do dbt build"
    finally:
        con.close()
