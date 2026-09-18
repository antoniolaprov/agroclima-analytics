import duckdb
import pytest

from dashboard import data


@pytest.fixture
def banco(tmp_path, monkeypatch):
    caminho = tmp_path / "w.duckdb"
    con = duckdb.connect(str(caminho))
    con.execute("create table gold_safra_uf (uf varchar, cultura varchar, ano integer, producao double)")
    con.execute("insert into gold_safra_uf values ('PR','soja',2024,18689393), ('MT','soja',2024,38396410)")
    con.close()
    monkeypatch.setattr(data.config, "DUCKDB_PATH", caminho)
    return caminho


def test_consultar_retorna_dataframe(banco):
    df = data.consultar("select * from gold_safra_uf order by uf")
    assert list(df["uf"]) == ["MT", "PR"]


def test_consultar_aceita_parametros(banco):
    df = data.consultar("select * from gold_safra_uf where uf = ?", ["PR"])
    assert len(df) == 1


def test_consultar_nao_deixa_conexao_aberta(banco):
    data.consultar("select 1")
    duckdb.connect(str(banco)).close()
