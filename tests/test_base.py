import pandas as pd
from src.ingestion import base


def test_write_parquet_adiciona_colunas_de_controle(tmp_path, monkeypatch):
    monkeypatch.setattr(base.config, "BRONZE_DIR", tmp_path)
    df = pd.DataFrame({"a": [1, 2]})

    caminho = base.write_parquet(df, "teste", "http://exemplo/x")

    lido = pd.read_parquet(caminho)
    assert list(lido["a"]) == [1, 2]
    assert lido["_source_url"].unique().tolist() == ["http://exemplo/x"]
    assert lido["_ingested_at"].notna().all()


def test_write_parquet_com_particao_cria_subpasta(tmp_path, monkeypatch):
    monkeypatch.setattr(base.config, "BRONZE_DIR", tmp_path)
    df = pd.DataFrame({"a": [1]})

    caminho = base.write_parquet(df, "clima", "http://exemplo/x", particao="2026")

    assert caminho.parent.name == "ano=2026"
    assert caminho.parent.parent.name == "clima"
