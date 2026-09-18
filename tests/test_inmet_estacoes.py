import json
from pathlib import Path

import responses

from src import config
from src.ingestion import inmet_api

FIXTURE = Path(__file__).parent / "fixtures" / "estacoes.json"


@responses.activate
def test_fetch_estacoes_tipa_colunas_numericas():
    responses.add(
        responses.GET,
        config.INMET_ESTACOES_URL,
        json=json.loads(FIXTURE.read_text(encoding="utf-8")),
        status=200,
    )

    df = inmet_api.fetch_estacoes()

    assert len(df) == 2
    assert df["latitude"].dtype.kind == "f"
    assert df.loc[df["cd_estacao"] == "A001", "latitude"].item() == -15.78944444
    assert set(df.columns) >= {"cd_estacao", "uf", "nome", "latitude", "longitude", "altitude", "situacao"}


@responses.activate
def test_fetch_estacoes_preserva_estacoes_nao_operantes():
    responses.add(
        responses.GET,
        config.INMET_ESTACOES_URL,
        json=json.loads(FIXTURE.read_text(encoding="utf-8")),
        status=200,
    )

    df = inmet_api.fetch_estacoes()

    assert set(df["situacao"]) == {"Operante", "Pane"}
