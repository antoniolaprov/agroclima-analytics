import numpy as np
import pandas as pd
import pytest

from src.ml import experimentos, modelos, validacao


class Espiao:
    """Modelo que anota os anos que viu no treino."""

    nome = "espiao"
    vistos: list = []

    def fit(self, X, y):
        Espiao.vistos.append((int(X["ano"].max()), None))
        return self

    def predict(self, X):
        Espiao.vistos[-1] = (Espiao.vistos[-1][0], int(X["ano"].min()))
        return np.zeros(len(X))


def _tabela(anos=range(2000, 2012)):
    linhas = [
        {"uf": uf, "cultura": "soja", "ano": a, "rendimento": 3000.0,
         "tendencia_log": np.log(3000.0), "anomalia": 0.1 * ((a + i) % 3 - 1)}
        for i, uf in enumerate(["MT", "PR", "RS"]) for a in anos
    ]
    return pd.DataFrame(linhas)


def test_treino_nunca_ve_o_ano_de_teste_nem_os_seguintes():
    Espiao.vistos = []
    tabela = _tabela()
    validacao.rolling_origin(tabela, Espiao, validacao.anos_de_teste(tabela))
    assert Espiao.vistos
    assert all(max_treino < ano_teste for max_treino, ano_teste in Espiao.vistos)


def test_anos_de_teste_reservam_os_primeiros_para_treino():
    assert validacao.anos_de_teste(_tabela(), min_anos_treino=5) == list(range(2005, 2012))


def test_skill_da_referencia_e_zero():
    tabela = _tabela()
    ref = validacao.rolling_origin(tabela, modelos.Tendencia, [2008, 2009])
    assert validacao.metricas(ref, ref)["skill"] == pytest.approx(0)


def test_previsao_perfeita_tem_skill_um():
    tabela = _tabela()
    ref = validacao.rolling_origin(tabela, modelos.Tendencia, [2008, 2009])
    perfeita = ref.assign(previsto=ref["anomalia"])
    assert validacao.metricas(perfeita, ref)["skill"] == pytest.approx(1)


def test_rendimento_previsto_volta_para_kg_ha():
    tabela = _tabela()
    p = validacao.rolling_origin(tabela, modelos.Tendencia, [2008])
    assert p["rendimento_previsto"].to_numpy() == pytest.approx(3000.0)


def test_bootstrap_e_reprodutivel_e_contem_o_skill():
    tabela = _tabela()
    ref = validacao.rolling_origin(tabela, modelos.Tendencia, list(range(2005, 2012)))
    meio = ref.assign(previsto=ref["anomalia"] * 0.5)
    ic1 = validacao.skill_bootstrap(meio, ref, semente=3)
    ic2 = validacao.skill_bootstrap(meio, ref, semente=3)
    skill = validacao.metricas(meio, ref)["skill"]
    assert ic1 == ic2
    assert ic1[0] <= skill <= ic1[1]


def test_recall_de_quebras():
    tabela = _tabela()
    ref = validacao.rolling_origin(tabela, modelos.Tendencia, [2008])
    ref.loc[0, "anomalia"] = np.log(0.8)
    acerta = ref.assign(previsto=np.where(ref.index == 0, np.log(0.85), 0.0))
    m = validacao.metricas(acerta)
    assert m["n_quebras"] == 1 and m["recall_quebras"] == 1.0


def test_lightgbm_acha_o_sinal_de_chuva_e_ablacoes_se_comportam(dados_sinteticos):
    # Nos dados sinteticos a anomalia depende so da chuva da fase 2.
    r = experimentos.rodar(dados_sinteticos)
    skill = r["metricas"].set_index("experimento")["skill"]
    assert skill["lgbm_completo"] > 0.3
    assert skill["lgbm_sem_clima"] < 0.1
    assert skill["lgbm_h1"] < 0.1 < skill["lgbm_h2"]


def test_experimentos_usam_as_mesmas_safras(dados_sinteticos):
    r = experimentos.rodar(dados_sinteticos)
    tamanhos = r["metricas"].set_index("experimento")["n"]
    assert tamanhos.nunique() == 1
