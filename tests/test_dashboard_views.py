import importlib

import duckdb
import pytest
from streamlit.testing.v1 import AppTest

from dashboard import data
from dashboard.views import clima, clima_safra, overview, safra


@pytest.fixture
def banco_gold(tmp_path, monkeypatch):
    """DuckDB temporario com as tres tabelas Gold, no formato que as views
    esperam. Substitui data/warehouse.duckdb (gitignored) para que a suite
    passe num clone limpo, sem depender do pipeline ter rodado antes."""
    caminho = tmp_path / "warehouse.duckdb"
    con = duckdb.connect(str(caminho))
    con.execute(
        """
        create table gold_safra_uf (
            uf varchar, uf_codigo varchar, cultura varchar, ano integer,
            area_plantada double, area_colhida double, producao double,
            rendimento double, var_producao_aa double, var_rendimento_aa double
        )
        """
    )
    con.execute(
        """
        insert into gold_safra_uf values
            ('DF', '53', 'soja', 2022, 1000, 950, 3000, 3200, null, null),
            ('DF', '53', 'soja', 2023, 1050, 980, 3100, 3250, 3.33, 1.56),
            ('SP', '35', 'soja', 2023, 800, 760, 2400, 3150, null, null),
            ('MG', '31', 'soja', 2023, 700, 650, 2000, 3080, null, null),
            ('MT', '51', 'soja', 2023, 5000, 4800, 15000, 3400, null, null),
            ('PR', '41', 'soja', 2023, 4000, 3800, 12000, 3300, null, null),
            ('RS', '43', 'soja', 2023, 3000, 2900, 9000, 3100, null, null)
        """
    )
    con.execute(
        """
        create table gold_clima_uf_mensal (
            uf varchar, ano integer, mes integer, temp_media double, temp_max double,
            temp_min double, precipitacao double, dias_sem_chuva integer, n_estacoes integer,
            temp_media_movel_3m double, anomalia_temp double, anomalia_precip double
        )
        """
    )
    con.execute(
        """
        insert into gold_clima_uf_mensal values
            ('DF', 2023, 1, 24.5, 30.0, 18.0, 120.0, 5, 1, 24.5, 0.2, -5.0),
            ('SP', 2023, 1, 23.0, 28.0, 17.0, 150.0, 3, 1, 23.0, -0.3, 4.0),
            ('MG', 2023, 1, 22.0, 27.0, 16.0, 140.0, 4, 1, 22.0, 0.1, 2.0)
        """
    )
    con.execute(
        """
        create table gold_clima_safra (
            uf varchar, cultura varchar, ano integer, rendimento double,
            precip_ciclo double, temp_media_ciclo double, n_estacoes integer,
            meses_observados integer, meses_esperados integer
        )
        """
    )
    con.execute(
        """
        insert into gold_clima_safra values
            ('DF', 'soja', 2023, 3200, 480.0, 23.5, 1, 6, 6),
            ('SP', 'soja', 2023, 3150, 510.0, 22.8, 1, 6, 6),
            ('MG', 'soja', 2023, 3080, 495.0, 22.1, 1, 6, 6)
        """
    )
    con.close()

    monkeypatch.setattr(data.config, "DUCKDB_PATH", caminho)
    data.safra.clear()
    data.clima_mensal.clear()
    data.clima_safra.clear()
    return caminho


def test_views_importam_sem_erro():
    for modulo in (overview, clima, safra, clima_safra):
        importlib.reload(modulo)
        assert hasattr(modulo, "render")


def test_overview_usa_safra_com_colunas_esperadas(banco_gold):
    df = data.safra(("DF", "SP", "MG"), ("soja", "milho", "cafe", "cana"), 2022, 2026)
    colunas_esperadas = {
        "uf", "uf_codigo", "cultura", "ano", "area_plantada", "area_colhida",
        "producao", "rendimento", "var_producao_aa", "var_rendimento_aa",
    }
    assert colunas_esperadas.issubset(set(df.columns))


def test_clima_usa_clima_mensal_com_colunas_esperadas(banco_gold):
    df = data.clima_mensal(("DF", "SP", "MG"), 2022, 2026)
    colunas_esperadas = {
        "uf", "ano", "mes", "temp_media", "temp_max", "temp_min", "precipitacao",
        "dias_sem_chuva", "n_estacoes", "temp_media_movel_3m", "anomalia_temp",
        "anomalia_precip",
    }
    assert colunas_esperadas.issubset(set(df.columns))
    if not df.empty:
        assert (df["ano"].between(2022, 2026)).all()


def test_safra_usa_safra_com_dados_reais(banco_gold):
    df = data.safra(("DF", "SP", "MG"), ("soja",), 2022, 2026)
    assert not df.empty
    assert {"uf", "ano", "producao", "rendimento", "var_producao_aa"}.issubset(df.columns)


def test_safra_filtra_pelo_intervalo_de_anos(banco_gold):
    df = data.safra(("DF",), ("soja",), 2022, 2022)
    assert set(df["ano"]) == {2022}


def test_clima_safra_usa_clima_safra_com_colunas_esperadas(banco_gold):
    df = data.clima_safra(("soja", "milho", "cafe", "cana"), 2022, 2026)
    colunas_esperadas = {
        "uf", "cultura", "ano", "rendimento", "precip_ciclo", "temp_media_ciclo",
        "n_estacoes", "meses_observados", "meses_esperados",
    }
    assert colunas_esperadas.issubset(set(df.columns))


def test_app_sobe_com_filtros_padrao_sem_excecao(banco_gold):
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
