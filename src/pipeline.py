import logging
import subprocess
import sys

from scripts import exportar_web as _exportar_web
from src import config
from src.ingestion import inmet_api, sidra_api

log = logging.getLogger(__name__)

DBT_DIR = config.RAIZ / "dbt"


def ingerir(anos=None) -> dict:
    anos = list(config.ANOS_CLIMA) if anos is None else list(anos)
    return {
        "estacoes": inmet_api.ingest_estacoes(),
        "clima": inmet_api.ingest_clima(anos),
        "pam": sidra_api.ingest_pam(),
        "lspa": sidra_api.ingest_lspa(),
    }


def rodar_dbt() -> None:
    # cwd=DBT_DIR: profiles.yml e o external_location de sources.yml usam
    # caminhos relativos (ex.: "../data/warehouse.duckdb"), resolvidos pelo
    # DuckDB contra o diretorio de trabalho do processo, nao contra
    # --project-dir/--profiles-dir. Sem isso, rodar a partir da raiz do repo
    # aponta para um warehouse.duckdb e um data/bronze/ errados.
    resultado = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbt.cli.main",
            "build",
            "--project-dir",
            str(DBT_DIR),
            "--profiles-dir",
            str(DBT_DIR),
            "--no-use-colors",
        ],
        cwd=str(DBT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    # A saida do subprocesso nao chega sozinha ao log da tarefa no Airflow;
    # sem repassa-la, uma falha do dbt aparece so como "dbt build falhou".
    linhas = resultado.stdout.splitlines()
    for linha in linhas:
        log.info(linha)
    if resultado.returncode != 0:
        raise RuntimeError("dbt build falhou:\n" + "\n".join(linhas[-20:]))


def exportar_web() -> dict:
    return _exportar_web.exportar()


def main(anos=None) -> dict:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    resumo = ingerir(anos)
    rodar_dbt()
    resumo["web"] = exportar_web()
    log.info("pipeline concluido: %s", resumo)
    return resumo


if __name__ == "__main__":
    main()
