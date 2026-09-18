import importlib

import pytest
from streamlit.testing.v1 import AppTest

from dashboard import data
from dashboard.views import clima, clima_safra, overview, safra


def test_views_importam_sem_erro():
    for modulo in (overview, clima, safra, clima_safra):
        importlib.reload(modulo)
        assert hasattr(modulo, "render")


def test_overview_usa_safra_com_colunas_esperadas():
    df = data.safra(("DF", "SP", "MG"), ("soja", "milho", "cafe", "cana"))
    colunas_esperadas = {
        "uf", "uf_codigo", "cultura", "ano", "area_plantada", "area_colhida",
        "producao", "rendimento", "var_producao_aa", "var_rendimento_aa",
    }
    assert colunas_esperadas.issubset(set(df.columns))


def test_clima_usa_clima_mensal_com_colunas_esperadas():
    df = data.clima_mensal(("DF", "SP", "MG"), 2022, 2026)
    colunas_esperadas = {
        "uf", "ano", "mes", "temp_media", "temp_max", "temp_min", "precipitacao",
        "dias_sem_chuva", "n_estacoes", "temp_media_movel_3m", "anomalia_temp",
        "anomalia_precip",
    }
    assert colunas_esperadas.issubset(set(df.columns))
    if not df.empty:
        assert (df["ano"].between(2022, 2026)).all()


def test_safra_usa_safra_com_dados_reais():
    df = data.safra(("DF", "SP", "MG"), ("soja",))
    assert not df.empty
    assert {"uf", "ano", "producao", "rendimento", "var_producao_aa"}.issubset(df.columns)


def test_clima_safra_usa_clima_safra_com_colunas_esperadas():
    df = data.clima_safra(("soja", "milho", "cafe", "cana"))
    colunas_esperadas = {
        "uf", "cultura", "ano", "rendimento", "precip_ciclo", "temp_media_ciclo",
        "n_estacoes", "meses_observados", "meses_esperados",
    }
    assert colunas_esperadas.issubset(set(df.columns))


def test_app_sobe_com_filtros_padrao_sem_excecao():
    at = AppTest.from_file("dashboard/app.py")
    at.run(timeout=30)
    assert not at.exception


def test_filtro_vazio_nao_chama_a_camada_de_dados(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("data.consultar nao deveria ser chamado com filtro vazio")

    data.safra.clear()
    data.clima_mensal.clear()
    data.clima_safra.clear()
    monkeypatch.setattr(data, "consultar", boom)

    at = AppTest.from_file("dashboard/app.py")
    at.run(timeout=30)
    assert at.exception, "com filtros padrao a camada de dados deveria ser chamada"

    at.sidebar.multiselect[0].set_value([])
    at.run(timeout=30)

    assert not at.exception
    assert [w.value for w in at.warning] == ["Selecione ao menos uma UF e uma cultura."]
