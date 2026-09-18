import math
from pathlib import Path

import pandas as pd

from src.ingestion import inmet_api

FIXTURE = Path(__file__).parent / "fixtures" / "INMET_CO_DF_A001_BRASILIA_01-01-2026_A_31-08-2026.CSV"


def _parse():
    return inmet_api.parse_csv_estacao(FIXTURE.read_bytes(), FIXTURE.name)


def test_pula_metadados_e_le_tres_linhas():
    assert len(_parse()) == 3


def test_extrai_estacao_e_uf_do_nome_do_arquivo():
    df = _parse()
    assert set(df["cd_estacao"]) == {"A001"}
    assert set(df["uf"]) == {"DF"}


def test_converte_virgula_decimal():
    df = _parse()
    assert df.loc[0, "temperatura"] == 19.9
    assert df.loc[1, "precipitacao"] == 0.2


def test_decimal_iniciado_por_virgula():
    df = _parse()
    assert df.loc[1, "vento_velocidade"] == 0.8


def test_campo_vazio_vira_nulo():
    df = _parse()
    assert math.isnan(df.loc[2, "precipitacao"])


def test_sentinela_menos_9999_vira_nulo():
    df = _parse()
    assert math.isnan(df.loc[2, "temperatura"])


def test_hora_utc_vira_inteiro():
    df = _parse()
    assert list(df["hora_utc"]) == [0, 1, 2]


def test_data_vira_datetime():
    df = _parse()
    assert df["data"].dtype.kind == "M"
    assert df.loc[0, "data"] == pd.Timestamp("2026-01-01")
