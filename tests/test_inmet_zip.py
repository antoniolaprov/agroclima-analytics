import io
import zipfile

import responses

from src import config
from src.ingestion import inmet_api, manifest


def _url(ano):
    return config.INMET_ZIP_URL.format(ano=ano)


def _zip_de_uma_estacao():
    conteudo = (
        "REGIAO:;CO\nUF:;DF\nESTACAO:;BRASILIA\nCODIGO (WMO):;A001\n"
        "LATITUDE:;-15,7\nLONGITUDE:;-47,9\nALTITUDE:;1160\nDATA DE FUNDACAO:;07/05/00\n"
        "Data;Hora UTC;PRECIPITAÇÃO TOTAL, HORÁRIO (mm);"
        "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C);"
        "TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C);"
        "TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C);"
        "UMIDADE RELATIVA DO AR, HORARIA (%);"
        "VENTO, VELOCIDADE HORARIA (m/s);\n"
        "2026/01/01;0000 UTC;0;19,9;20,8;19,8;92;1,1;\n"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(
            "INMET_CO_DF_A001_BRASILIA_01-01-2026_A_31-08-2026.CSV",
            conteudo.encode("latin1"),
        )
    return buffer.getvalue()


@responses.activate
def test_zip_mudou_quando_nao_ha_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    responses.add(responses.HEAD, _url(2026), headers={"ETag": "v1"}, status=200)

    mudou, headers = inmet_api.zip_mudou(2026)

    assert mudou is True
    assert headers["etag"] == "v1"


@responses.activate
def test_zip_nao_mudou_quando_etag_igual(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    manifest.gravar("clima_2026", {"etag": "v1", "last_modified": None})
    responses.add(responses.HEAD, _url(2026), headers={"ETag": "v1"}, status=200)

    mudou, _ = inmet_api.zip_mudou(2026)

    assert mudou is False


@responses.activate
def test_zip_mudou_quando_etag_difere_mesmo_com_last_modified_igual(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    manifest.gravar("clima_2026", {"etag": "v1", "last_modified": "Wed, 01 Jan 2026 00:00:00 GMT"})
    responses.add(
        responses.HEAD,
        _url(2026),
        headers={"ETag": "v2", "Last-Modified": "Wed, 01 Jan 2026 00:00:00 GMT"},
        status=200,
    )

    mudou, _ = inmet_api.zip_mudou(2026)

    assert mudou is True


@responses.activate
def test_zip_mudou_quando_sem_etag_e_last_modified_difere(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    manifest.gravar("clima_2026", {"etag": None, "last_modified": "Wed, 01 Jan 2026 00:00:00 GMT"})
    responses.add(
        responses.HEAD,
        _url(2026),
        headers={"Last-Modified": "Thu, 02 Jan 2026 00:00:00 GMT"},
        status=200,
    )

    mudou, _ = inmet_api.zip_mudou(2026)

    assert mudou is True


@responses.activate
def test_zip_mudou_quando_resposta_sem_headers(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    manifest.gravar("clima_2026", {"etag": "v1", "last_modified": "Wed, 01 Jan 2026 00:00:00 GMT"})
    responses.add(responses.HEAD, _url(2026), status=200)

    mudou, _ = inmet_api.zip_mudou(2026)

    assert mudou is True


@responses.activate
def test_ingest_clima_pula_ano_sem_mudanca(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    monkeypatch.setattr(config, "BRONZE_DIR", tmp_path)
    manifest.gravar("clima_2026", {"etag": "v1", "last_modified": None})
    responses.add(responses.HEAD, _url(2026), headers={"ETag": "v1"}, status=200)

    assert inmet_api.ingest_clima([2026]) == {2026: 0}


@responses.activate
def test_ingest_clima_baixa_e_grava_quando_mudou(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    monkeypatch.setattr(config, "BRONZE_DIR", tmp_path)
    responses.add(responses.HEAD, _url(2026), headers={"ETag": "v2"}, status=200)
    responses.add(responses.GET, _url(2026), body=_zip_de_uma_estacao(), status=200)

    resultado = inmet_api.ingest_clima([2026])

    assert resultado == {2026: 1}
    assert (tmp_path / "clima_horario" / "ano=2026" / "dados.parquet").exists()
    assert manifest.ler("clima_2026")["etag"] == "v2"
