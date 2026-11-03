import numpy as np
import pandas as pd
import pytest

from src.ml import alvo


def _serie(rendimentos, inicio=2000, uf="MT", cultura="soja"):
    return pd.DataFrame(
        {"uf": uf, "cultura": cultura, "ano": range(inicio, inicio + len(rendimentos)),
         "rendimento": rendimentos}
    )


def test_serie_exponencial_tem_anomalia_zero():
    rend = 2000 * np.exp(0.03 * np.arange(20))
    df = alvo.calcular(_serie(rend))
    assert df["anomalia"].dropna().abs().max() == pytest.approx(0, abs=1e-9)


def test_anos_sem_historico_ficam_sem_anomalia():
    df = alvo.calcular(_serie(np.linspace(2000, 3000, 12)), min_anos=8)
    assert df["anomalia"].isna().sum() == 8
    assert df["anomalia"].iloc[8:].notna().all()


def test_tendencia_nao_usa_anos_futuros():
    rend = list(2000 * np.exp(0.02 * np.arange(20)))
    base = alvo.calcular(_serie(rend))
    rend[-1] *= 3
    alterada = alvo.calcular(_serie(rend))
    pd.testing.assert_series_equal(base["anomalia"].iloc[:-1], alterada["anomalia"].iloc[:-1])


def test_tendencia_usa_so_a_janela():
    anos = np.arange(2000, 2030, dtype=float)
    log_rend = np.where(anos < 2010, 5.0, 7.0)
    previsto = alvo.tendencia_passada(anos, log_rend, janela=10, min_anos=8)
    # 2025 so enxerga 2015-2024, todos em 7.0.
    assert previsto[anos == 2025][0] == pytest.approx(7.0)


def test_quebra_aparece_como_anomalia_negativa():
    rend = 2000 * np.exp(0.02 * np.arange(20))
    rend[15] *= 0.7
    df = alvo.calcular(_serie(rend))
    assert df.loc[15, "anomalia"] == pytest.approx(np.log(0.7), abs=1e-6)


def test_safra_anterior_so_com_ano_adjacente():
    df = _serie([1000, 1100, 1200, 1300])
    df.loc[2:, "ano"] += 1
    saida = alvo.calcular(df, min_anos=1)
    assert np.isnan(saida.loc[2, "rendimento_anterior"])
    assert saida.loc[3, "rendimento_anterior"] == 1200


def test_series_de_uf_e_cultura_sao_independentes():
    a = _serie(2000 * np.exp(0.02 * np.arange(15)), uf="MT")
    b = _serie(500 * np.exp(-0.01 * np.arange(15)), uf="RS")
    df = alvo.calcular(pd.concat([a, b]))
    assert df["anomalia"].dropna().abs().max() == pytest.approx(0, abs=1e-9)


def test_safra_nao_publicada_recebe_tendencia_sem_entrar_no_ajuste():
    rend = list(2000 * np.exp(0.02 * np.arange(15))) + [np.nan]
    df = alvo.calcular(_serie(rend))
    esperado = np.log(2000) + 0.02 * 15
    assert df["tendencia_log"].iloc[-1] == pytest.approx(esperado)
    assert np.isnan(df["anomalia"].iloc[-1])
