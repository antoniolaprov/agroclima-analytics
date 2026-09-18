import logging
import time
from pathlib import Path

import pandas as pd
import requests

from src import config

log = logging.getLogger(__name__)


def http_get(url: str, timeout: int = 60, tentativas: int = 3, **kwargs) -> requests.Response:
    for n in range(1, tentativas + 1):
        resposta = requests.get(url, timeout=timeout, **kwargs)
        if resposta.status_code < 500:
            resposta.raise_for_status()
            return resposta
        log.warning("tentativa %s falhou para %s (%s)", n, url, resposta.status_code)
        time.sleep(2 ** n)
    resposta.raise_for_status()
    return resposta


def write_parquet(df: pd.DataFrame, nome: str, source_url: str, particao: str | None = None) -> Path:
    df = df.copy()
    df["_ingested_at"] = pd.Timestamp.utcnow()
    df["_source_url"] = source_url

    destino = Path(config.BRONZE_DIR) / nome
    if particao is not None:
        destino = destino / f"ano={particao}"
    destino.mkdir(parents=True, exist_ok=True)

    caminho = destino / "dados.parquet"
    df.to_parquet(caminho, index=False)
    log.info("gravado %s (%s linhas)", caminho, len(df))
    return caminho
