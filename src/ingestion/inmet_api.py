import io
import logging
import re
import zipfile
from typing import Iterable

import pandas as pd
import requests

from src import config
from src.ingestion import base, manifest

log = logging.getLogger(__name__)

COLUNAS_ESTACAO = {
    "CD_ESTACAO": "cd_estacao",
    "DC_NOME": "nome",
    "SG_ESTADO": "uf",
    "VL_LATITUDE": "latitude",
    "VL_LONGITUDE": "longitude",
    "VL_ALTITUDE": "altitude",
    "CD_SITUACAO": "situacao",
    "DT_INICIO_OPERACAO": "inicio_operacao",
    "DT_FIM_OPERACAO": "fim_operacao",
}


def fetch_estacoes() -> pd.DataFrame:
    resposta = base.http_get(config.INMET_ESTACOES_URL)
    df = pd.DataFrame(resposta.json())

    faltando = set(COLUNAS_ESTACAO) - set(df.columns)
    if faltando:
        raise ValueError(f"resposta do INMET sem as colunas {sorted(faltando)}")

    df = df[list(COLUNAS_ESTACAO)].rename(columns=COLUNAS_ESTACAO)
    for coluna in ("latitude", "longitude", "altitude"):
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df


def ingest_estacoes() -> int:
    df = fetch_estacoes()
    base.write_parquet(df, "estacoes", config.INMET_ESTACOES_URL)
    return len(df)


SENTINELAS = {"", "-9999", "9999", "null"}

COLUNAS_CSV = {
    "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)": "precipitacao",
    "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)": "temperatura",
    "TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)": "temperatura_max",
    "TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)": "temperatura_min",
    "UMIDADE RELATIVA DO AR, HORARIA (%)": "umidade",
    "VENTO, VELOCIDADE HORARIA (m/s)": "vento_velocidade",
}

PADRAO_NOME = re.compile(r"INMET_[A-Z]{1,2}_([A-Z]{2})_([A-Z]\d{3})_")


def _para_float(valor: str) -> float:
    texto = str(valor).strip()
    if texto in SENTINELAS:
        return float("nan")
    return float(texto.replace(",", "."))


def parse_csv_estacao(conteudo: bytes, nome_arquivo: str) -> pd.DataFrame:
    achado = PADRAO_NOME.search(nome_arquivo)
    if achado is None:
        raise ValueError(f"nome de arquivo fora do padrao do INMET: {nome_arquivo}")
    uf, cd_estacao = achado.groups()

    texto = conteudo.decode("latin1")
    df = pd.read_csv(io.StringIO(texto), sep=";", skiprows=8, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]

    presentes = {orig: novo for orig, novo in COLUNAS_CSV.items() if orig in df.columns}
    if len(presentes) != len(COLUNAS_CSV):
        faltando = sorted(set(COLUNAS_CSV) - set(presentes))
        raise ValueError(f"CSV {nome_arquivo} sem as colunas {faltando}")

    saida = pd.DataFrame(
        {
            "cd_estacao": cd_estacao,
            "uf": uf,
            "data": pd.to_datetime(df["Data"], format="%Y/%m/%d"),
            "hora_utc": df["Hora UTC"].str.slice(0, 2).astype(int),
        }
    )
    for original, novo in presentes.items():
        saida[novo] = df[original].map(_para_float)
    return saida


def zip_mudou(ano: int) -> tuple[bool, dict]:
    url = config.INMET_ZIP_URL.format(ano=ano)
    cabecalho = requests.head(url, timeout=60, allow_redirects=True)
    cabecalho.raise_for_status()

    atual = {
        "etag": cabecalho.headers.get("ETag"),
        "last_modified": cabecalho.headers.get("Last-Modified"),
    }
    anterior = manifest.ler(f"clima_{ano}")
    if anterior is None:
        return True, atual
    if atual["etag"] and anterior.get("etag"):
        return atual["etag"] != anterior["etag"], atual
    if atual["last_modified"] and anterior.get("last_modified"):
        return atual["last_modified"] != anterior["last_modified"], atual
    return True, atual


def _ler_zip(conteudo: bytes) -> pd.DataFrame:
    partes = []
    with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
        for nome in z.namelist():
            if not nome.upper().endswith(".CSV"):
                continue
            try:
                partes.append(parse_csv_estacao(z.read(nome), nome.split("/")[-1]))
            except ValueError as erro:
                log.warning("ignorando %s: %s", nome, erro)
    if not partes:
        raise ValueError("nenhum CSV valido no zip")
    return pd.concat(partes, ignore_index=True)


def ingest_clima(anos: Iterable[int]) -> dict[int, int]:
    resultado = {}
    for ano in anos:
        mudou, headers = zip_mudou(ano)
        if not mudou:
            log.info("clima %s sem mudanca, pulando", ano)
            resultado[ano] = 0
            continue

        url = config.INMET_ZIP_URL.format(ano=ano)
        df = _ler_zip(base.http_get(url, timeout=600).content)
        base.write_parquet(df, "clima_horario", url, particao=str(ano))
        manifest.gravar(f"clima_{ano}", headers)
        resultado[ano] = len(df)
    return resultado
