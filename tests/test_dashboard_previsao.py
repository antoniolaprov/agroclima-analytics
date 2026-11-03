import json

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard import data
from src import config
from src.ml import prever, treino


@pytest.fixture(scope="module")
def pasta_modelos(tmp_path_factory, dados_sinteticos):
    destino = tmp_path_factory.mktemp("modelos")
    treino.main(destino=destino, usar_mlflow=False, dados=dados_sinteticos)
    pendentes = dict(dados_sinteticos)
    pendentes["safra"] = dados_sinteticos["safra"].query("ano < 2026")
    prever.prever(pendentes, destino / "atual").to_csv(destino / "previsoes.csv", index=False)
    return destino


@pytest.fixture
def sem_warehouse(monkeypatch):
    # As outras paginas nao entram nestes testes; a de abertura so precisa
    # nao quebrar sem o DuckDB.
    monkeypatch.setattr(data, "consultar", lambda *a, **k: pd.DataFrame())
    for funcao in (data.safra, data.clima_mensal, data.clima_safra, data.producao_por_uf,
                   data.previsoes, data.modelo_atual):
        funcao.clear()


def _abrir_previsao(ufs=("MT", "PR", "RS"), culturas=("soja",)):
    at = AppTest.from_file("dashboard/app.py")
    at.run(timeout=30)
    at.sidebar.multiselect[0].set_value(list(ufs))
    at.sidebar.multiselect[1].set_value(list(culturas))
    at.sidebar.radio[0].set_value("Previsao")
    at.run(timeout=60)
    return at


def test_sem_modelo_explica_como_gerar(sem_warehouse, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MODELOS_DIR", tmp_path)
    at = _abrir_previsao()
    assert not at.exception
    assert "python -m src.ml.treino" in at.info[0].value


def test_mostra_mapa_e_barras_com_modelo(sem_warehouse, pasta_modelos, monkeypatch):
    monkeypatch.setattr(config, "MODELOS_DIR", pasta_modelos)
    at = _abrir_previsao()
    assert not at.exception, at.exception
    tipos = [json.loads(g.proto.spec)["data"][0]["type"] for g in at.get("plotly_chart")]
    assert tipos[0] == "choropleth"
    assert "bar" in tipos
    assert at.metric[0].label == "Skill na validacao"


def test_escolhe_entre_safras_pendentes(sem_warehouse, pasta_modelos, monkeypatch):
    # Com clima ate dez/2026, a soja tem a safra 2026 completa e a 2027 so no
    # primeiro terco.
    monkeypatch.setattr(config, "MODELOS_DIR", pasta_modelos)
    at = _abrir_previsao()
    radio = [r for r in at.radio if r.label == "Safra"][0]
    assert list(radio.options) == ["Safra 2026 (ciclo completo)", "Safra 2027 (1/3 do ciclo observado)"]


def test_avisa_quando_o_modelo_nao_ganha_da_tendencia(sem_warehouse, pasta_modelos, tmp_path, monkeypatch):
    import shutil

    copia = tmp_path / "modelos"
    shutil.copytree(pasta_modelos, copia)
    meta = copia / "atual" / "metadados.json"
    conteudo = json.loads(meta.read_text(encoding="utf-8"))
    conteudo["metricas"]["skill"] = -0.05
    meta.write_text(json.dumps(conteudo), encoding="utf-8")
    monkeypatch.setattr(config, "MODELOS_DIR", copia)

    at = _abrir_previsao()
    assert any("nao ganhou da tendencia" in w.value for w in at.warning)


def test_cultura_sem_previsao(sem_warehouse, pasta_modelos, monkeypatch):
    monkeypatch.setattr(config, "MODELOS_DIR", pasta_modelos)
    at = _abrir_previsao(culturas=("cafe",))
    assert not at.exception
    assert "nao tem previsao pendente" in at.info[0].value
