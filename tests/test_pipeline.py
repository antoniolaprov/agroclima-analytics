import pytest

from src import config, pipeline


def test_ingerir_chama_todas_as_fontes(monkeypatch):
    chamadas = []
    monkeypatch.setattr(pipeline.inmet_api, "ingest_estacoes", lambda: chamadas.append("estacoes") or 674)
    monkeypatch.setattr(pipeline.inmet_api, "ingest_clima", lambda anos: chamadas.append("clima") or {2026: 10})
    monkeypatch.setattr(pipeline.sidra_api, "ingest_pam", lambda: chamadas.append("pam") or 100)
    monkeypatch.setattr(pipeline.sidra_api, "ingest_lspa", lambda: chamadas.append("lspa") or 50)

    resumo = pipeline.ingerir([2026])

    assert chamadas == ["estacoes", "clima", "pam", "lspa"]
    assert resumo == {"estacoes": 674, "clima": {2026: 10}, "pam": 100, "lspa": 50}


def test_ingerir_usa_anos_do_config_por_padrao(monkeypatch):
    recebido = {}
    monkeypatch.setattr(pipeline.inmet_api, "ingest_estacoes", lambda: 0)
    monkeypatch.setattr(pipeline.inmet_api, "ingest_clima", lambda anos: recebido.setdefault("anos", list(anos)) or {})
    monkeypatch.setattr(pipeline.sidra_api, "ingest_pam", lambda: 0)
    monkeypatch.setattr(pipeline.sidra_api, "ingest_lspa", lambda: 0)

    pipeline.ingerir()

    assert recebido["anos"] == list(config.ANOS_CLIMA)


def test_rodar_dbt_propaga_falha(monkeypatch):
    def falso_run(*args, **kwargs):
        class R:
            returncode = 1
        return R()

    monkeypatch.setattr(pipeline.subprocess, "run", falso_run)

    with pytest.raises(RuntimeError, match="dbt build falhou"):
        pipeline.rodar_dbt()
