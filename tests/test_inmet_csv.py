import math
from pathlib import Path

import pandas as pd
import pytest

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


FIXTURE_ANTIGA = Path(__file__).parent / "fixtures" / "INMET_CO_DF_A001_BRASILIA_07-05-2000_A_31-12-2010.CSV"


def _parse_antigo():
    return inmet_api.parse_csv_estacao(FIXTURE_ANTIGA.read_bytes(), FIXTURE_ANTIGA.name)


def test_layout_ate_2018_le_data_com_hifen():
    df = _parse_antigo()
    assert df.loc[0, "data"] == pd.Timestamp("2010-01-01")


def test_layout_ate_2018_le_hora_com_dois_pontos():
    assert list(_parse_antigo()["hora_utc"]) == [0, 1, 2]


def test_layout_ate_2018_mantem_as_medicoes():
    novo, antigo = _parse(), _parse_antigo()
    colunas = ["precipitacao", "temperatura", "umidade", "vento_velocidade"]
    pd.testing.assert_frame_equal(novo[colunas], antigo[colunas])


def test_layout_desconhecido_e_rejeitado():
    texto = FIXTURE.read_bytes().decode("latin1").replace("Data;Hora UTC;", "Dia;Hora;", 1)
    with pytest.raises(ValueError, match="data/hora"):
        inmet_api.parse_csv_estacao(texto.encode("latin1"), FIXTURE.name)
