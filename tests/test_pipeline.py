import sys

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


def test_rodar_dbt_invoca_dbt_como_modulo_do_interpretador(monkeypatch):
    comandos = []

    def falso_run(cmd, **kwargs):
        comandos.append(cmd)

        class R:
            returncode = 0
        return R()

    monkeypatch.setattr(pipeline.subprocess, "run", falso_run)

    pipeline.rodar_dbt()

    assert len(comandos) == 1
    cmd = comandos[0]
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "dbt.cli.main"]
    assert cmd[0] != "dbt"
    assert "build" in cmd
