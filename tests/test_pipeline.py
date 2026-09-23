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


def test_rodar_dbt_propaga_falha_com_o_motivo_dado_pelo_dbt(monkeypatch):
    def falso_run(*args, **kwargs):
        class R:
            returncode = 1
            stdout = "Running with dbt=1.8.8\nFAIL 3 assert_algum_teste\nDone. PASS=40 ERROR=1\n"
        return R()

    monkeypatch.setattr(pipeline.subprocess, "run", falso_run)

    with pytest.raises(RuntimeError, match="dbt build falhou") as erro:
        pipeline.rodar_dbt()
    assert "FAIL 3 assert_algum_teste" in str(erro.value)


def test_rodar_dbt_leva_a_saida_do_dbt_para_o_log(monkeypatch, caplog):
    def falso_run(*args, **kwargs):
        class R:
            returncode = 0
            stdout = "Done. PASS=46 WARN=0 ERROR=0\n"
        return R()

    monkeypatch.setattr(pipeline.subprocess, "run", falso_run)

    with caplog.at_level("INFO", logger=pipeline.log.name):
        pipeline.rodar_dbt()
    assert "Done. PASS=46 WARN=0 ERROR=0" in caplog.text


def test_rodar_dbt_invoca_dbt_como_modulo_do_interpretador(monkeypatch):
    comandos = []

    def falso_run(cmd, **kwargs):
        comandos.append(cmd)

        class R:
            returncode = 0
            stdout = ""
        return R()

    monkeypatch.setattr(pipeline.subprocess, "run", falso_run)

    pipeline.rodar_dbt()

    assert len(comandos) == 1
    cmd = comandos[0]
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "dbt.cli.main"]
    assert cmd[0] != "dbt"
    assert "build" in cmd


def test_main_exporta_o_site_depois_do_dbt(monkeypatch):
    ordem = []
    monkeypatch.setattr(pipeline, "ingerir", lambda anos=None: ordem.append("ingerir") or {})
    monkeypatch.setattr(pipeline, "rodar_dbt", lambda: ordem.append("dbt"))
    monkeypatch.setattr(pipeline, "exportar_web", lambda: ordem.append("web") or {})

    pipeline.main()

    assert ordem == ["ingerir", "dbt", "web"]
