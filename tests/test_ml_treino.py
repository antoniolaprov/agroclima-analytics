import json

import duckdb
import numpy as np
import pytest

from src.ml import dados as dados_ml
from src.ml import prever, treino


@pytest.fixture(scope="module")
def treinado(tmp_path_factory, dados_sinteticos):
    destino = tmp_path_factory.mktemp("modelos")
    resumo = treino.main(destino=destino, usar_mlflow=False, dados=dados_sinteticos)
    return destino, resumo


def test_primeira_versao_e_promovida(treinado):
    destino, resumo = treinado
    assert resumo["promovido"]
    assert (destino / "atual" / "modelo_h3.joblib").exists()


def test_grava_artefatos_e_model_card(treinado):
    atual = treinado[0] / "atual"
    for nome in ("README.md", "relatorio.md", "metricas.csv", "importancia.csv",
                 "figuras/skill.png", "modelo_h1.joblib", "modelo_h2.joblib"):
        assert (atual / nome).exists(), nome
    card = (atual / "README.md").read_text(encoding="utf-8")
    assert card.startswith("---\nlanguage: pt")


def test_metadados_tem_skill_e_variaveis(treinado):
    meta = json.loads((treinado[0] / "atual" / "metadados.json").read_text(encoding="utf-8"))
    assert meta["metricas"]["skill"] == pytest.approx(treinado[1]["skill"])
    assert "chuva_rel_f2" in meta["variaveis"]["3"]


def test_shap_aponta_a_chuva_da_fase_2(treinado):
    imp = (treinado[0] / "atual" / "importancia.csv").read_text().splitlines()
    assert "chuva" in imp[1] and "f1" not in imp[1]


@pytest.mark.parametrize(
    "novo, anterior, esperado",
    [(0.30, None, True), (0.30, 0.31, True), (0.30, 0.40, False), (0.50, 0.40, True)],
)
def test_portao_de_promocao(novo, anterior, esperado):
    assert treino.decidir_promocao(novo, anterior, tolerancia=0.02) is esperado


def test_previsao_cobre_safras_ainda_nao_publicadas(treinado, dados_sinteticos):
    dados = dict(dados_sinteticos)
    dados["safra"] = dados_sinteticos["safra"].query("ano < 2026")
    p = prever.prever(dados, treinado[0] / "atual")
    assert set(p["ano"]) >= {2026}
    assert p.loc[p["ano"] == 2026, "horizonte"].eq(3).all()
    assert np.isfinite(p["rendimento_previsto"]).all()


def test_previsao_sem_safra_pendente_e_vazia(treinado, dados_sinteticos):
    dados = dict(dados_sinteticos)
    dados["clima"] = dados_sinteticos["clima"].query("ano <= 2025 and not (ano == 2025 and mes >= 9)")
    assert prever.prever(dados, treinado[0] / "atual").empty


def test_carrega_do_warehouse(tmp_path, dados_sinteticos):
    caminho = tmp_path / "w.duckdb"
    con = duckdb.connect(str(caminho))
    safra = dados_sinteticos["safra"]
    clima = dados_sinteticos["clima"]
    ciclo = dados_sinteticos["ciclo"]
    con.execute("create table gold_safra_uf as select * from safra")
    con.execute("create table gold_clima_uf_mensal as select * from clima")
    con.execute("create table ciclo_cultura as select * from ciclo")
    con.close()
    carregado = dados_ml.carregar(caminho)
    assert len(carregado["safra"]) == len(safra)
    assert set(carregado["clima"].columns) >= {"precipitacao", "temp_max", "dias_sem_chuva"}
