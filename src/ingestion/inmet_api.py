import logging

import pandas as pd

from src import config
from src.ingestion import base

log = logging.getLogger(__name__)

COLUNAS_ESTACAO = {
    "CD_ESTACAO": "cd_estacao",
    "DC_NOME": "nome",
    "SG_ESTADO": "uf",
    "VL_LATITUDE": "latitude",
    "VL_LONGITUDE": "longitude",
    "VL_ALTITUDE": "altitude",
    "CD_SITUACAO": "situacao",
    "DT_INICIO_OPERACAO": "inicio_operacao",
    "DT_FIM_OPERACAO": "fim_operacao",
}


def fetch_estacoes() -> pd.DataFrame:
    resposta = base.http_get(config.INMET_ESTACOES_URL)
    df = pd.DataFrame(resposta.json())

    faltando = set(COLUNAS_ESTACAO) - set(df.columns)
    if faltando:
        raise ValueError(f"resposta do INMET sem as colunas {sorted(faltando)}")

    df = df[list(COLUNAS_ESTACAO)].rename(columns=COLUNAS_ESTACAO)
    for coluna in ("latitude", "longitude", "altitude"):
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df


def ingest_estacoes() -> int:
    df = fetch_estacoes()
    base.write_parquet(df, "estacoes", config.INMET_ESTACOES_URL)
    return len(df)
