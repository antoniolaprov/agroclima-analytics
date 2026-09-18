import logging
import subprocess

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
    resultado = subprocess.run(
        ["dbt", "build", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)],
        check=False,
    )
    if resultado.returncode != 0:
        raise RuntimeError("dbt build falhou")


def main(anos=None) -> dict:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    resumo = ingerir(anos)
    rodar_dbt()
    log.info("pipeline concluido: %s", resumo)
    return resumo


if __name__ == "__main__":
    main()
