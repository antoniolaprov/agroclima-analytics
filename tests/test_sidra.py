import json
import math
from pathlib import Path

from src.ingestion import sidra_api

FIXTURE = Path(__file__).parent / "fixtures" / "sidra_pam.json"
MAPA = {"40124": "soja"}


def _parse():
    return sidra_api.parse_resposta(json.loads(FIXTURE.read_text(encoding="utf-8")), MAPA)


def test_achata_para_linhas_longas():
    df = _parse()
    assert len(df) == 4
    assert set(df["variavel"]) == {"214", "112"}


def test_mapeia_cultura_pelo_codigo():
    assert set(_parse()["cultura"]) == {"soja"}


def test_converte_valor_para_float():
    df = _parse()
    linha = df[(df["uf_codigo"] == "41") & (df["variavel"] == "214")]
    assert linha["valor"].item() == 18689393.0


def test_reticencias_vira_nulo():
    df = _parse()
    linha = df[(df["uf_codigo"] == "51") & (df["variavel"] == "112")]
    assert math.isnan(linha["valor"].item())


def test_periodo_preservado():
    assert set(_parse()["periodo"]) == {"2024"}
