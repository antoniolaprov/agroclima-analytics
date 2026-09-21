import json
import math
from pathlib import Path

import pandas as pd

from src import config
from src.ingestion import sidra_api

FIXTURE = Path(__file__).parent / "fixtures" / "sidra_pam.json"
MAPA = {"40124": "soja", "40122": "milho", "40139": "cafe"}


def _parse():
    return sidra_api.parse_resposta(json.loads(FIXTURE.read_text(encoding="utf-8")), MAPA)


def test_achata_para_linhas_longas():
    df = _parse()
    assert len(df) == 12
    assert set(df["variavel"]) == {"214", "112"}


def test_mapeia_cultura_pelo_codigo():
    assert set(_parse()["cultura"]) == {"soja", "milho", "cafe"}


def test_converte_valor_para_float():
    df = _parse()
    linha = df[(df["uf_codigo"] == "41") & (df["variavel"] == "214") & (df["cultura"] == "soja")]
    assert linha["valor"].item() == 18689393.0


def test_reticencias_vira_nulo():
    df = _parse()
    linha = df[(df["uf_codigo"] == "51") & (df["variavel"] == "112") & (df["cultura"] == "soja")]
    assert math.isnan(linha["valor"].item())


def test_periodo_preservado():
    assert set(_parse()["periodo"]) == {"2024"}


def test_valores_nao_se_misturam_entre_culturas():
    df = _parse()

    def valor(uf, cultura, variavel):
        linha = df[(df["uf_codigo"] == uf) & (df["cultura"] == cultura) & (df["variavel"] == variavel)]
        return linha["valor"].item()

    assert valor("41", "soja", "214") == 18689393.0
    assert valor("41", "milho", "214") == 6500000.0
    assert valor("51", "cafe", "214") == 12000.0
    assert valor("41", "milho", "112") == 5500.0
    assert valor("51", "milho", "112") == 6100.0

    assert valor("41", "milho", "214") != valor("41", "soja", "214")


def test_montar_url_constroi_string_esperada():
    url = sidra_api.montar_url("5457", "all", ["214", "112"], "782", ["40124", "40122"])
    esperado = (
        f"{config.SIDRA_BASE}/5457/periodos/all"
        "/variaveis/214|112"
        "?localidades=N3[all]&classificacao=782[40124,40122]"
    )
    assert url == esperado


def test_ingest_lspa_pede_so_os_meses_da_janela_do_clima(monkeypatch):
    urls = []

    class Resposta:
        def json(self):
            return []

    monkeypatch.setattr(sidra_api.base, "http_get", lambda url, **kw: urls.append(url) or Resposta())
    monkeypatch.setattr(sidra_api, "parse_resposta", lambda payload, mapa: pd.DataFrame({"cultura_codigo": []}))
    monkeypatch.setattr(sidra_api.base, "write_parquet", lambda *a, **kw: None)
    monkeypatch.setattr(sidra_api.config, "ANOS_CLIMA", (2022, 2023, 2024))

    sidra_api.ingest_lspa()

    assert "/6588/periodos/202201-202412/" in urls[0]
