"""Gera dados fabricados na camada Bronze para desenvolvimento local do dbt.

Nao chama as APIs do INMET ou do SIDRA. Escreve Parquet diretamente em
data/bronze/ com o mesmo formato produzido pela ingestao real (src/ingestion),
incluindo as colunas _ingested_at e _source_url adicionadas por
src.ingestion.base.write_parquet.

Uso: python scripts/seed_bronze_dev.py
"""

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config

AGORA = pd.Timestamp.utcnow()
SOURCE_URL = "seed:local-dev"


def _com_metadados(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_ingested_at"] = AGORA
    df["_source_url"] = SOURCE_URL
    return df


def gerar_estacoes() -> pd.DataFrame:
    linhas = [
        # cd_estacao, nome, uf, latitude, longitude, altitude, situacao, inicio_operacao, fim_operacao
        ("A001", "BRASILIA", "DF", -15.789, -47.925, 1160.0, "Operante", "2000-01-01", None),
        ("A002", "SAO PAULO - MIRANTE", "SP", -23.496, -46.620, 792.0, "Operante", "2001-05-10", None),
        ("A003", "BELO HORIZONTE - PAMPULHA", "MG", -19.884, -43.969, 780.0, "Operante", "2003-03-20", None),
        # exclusao esperada: situacao diferente de Operante
        ("A004", "BRASILIA - AEROPORTO", "DF", -15.865, -47.918, 1063.0, "Pane", "1998-07-01", None),
        # exclusao esperada: fim_operacao preenchido
        ("A005", "CAMPINAS", "SP", -22.905, -47.048, 640.0, "Operante", "1999-02-15", "2025-01-01"),
    ]
    df = pd.DataFrame(
        linhas,
        columns=[
            "cd_estacao",
            "nome",
            "uf",
            "latitude",
            "longitude",
            "altitude",
            "situacao",
            "inicio_operacao",
            "fim_operacao",
        ],
    )
    return _com_metadados(df)


def gerar_clima_horario() -> pd.DataFrame:
    linhas = []

    def add_dia(cd_estacao: str, uf: str, data: dt.date, horas: range):
        for hora in horas:
            base = 20 + (hora % 12) * 0.5
            linhas.append(
                {
                    "cd_estacao": cd_estacao,
                    "uf": uf,
                    "data": data,
                    "hora_utc": hora,
                    "precipitacao": round(0.2 * (hora % 3), 1),
                    "temperatura": round(base, 1),
                    "temperatura_max": round(base + 1.0, 1),
                    "temperatura_min": round(base - 1.0, 1),
                    "umidade": float(60 + (hora % 10)),
                    "vento_velocidade": round(1.5 + (hora % 5) * 0.3, 1),
                }
            )

    # A001: um dia com as 24 horas completas e outro com 20 horas.
    add_dia("A001", "DF", dt.date(2026, 1, 1), range(0, 24))
    add_dia("A001", "DF", dt.date(2026, 1, 2), range(0, 20))

    # A002: um dia com poucas horas observadas (< 18, deve ser descartado
    # pelo corte de stg_clima_diario) e outro dia completo.
    add_dia("A002", "SP", dt.date(2026, 1, 1), range(0, 10))
    add_dia("A002", "SP", dt.date(2026, 1, 2), range(0, 24))

    # A003: um dia logo acima do corte de 18 horas.
    add_dia("A003", "MG", dt.date(2026, 1, 1), range(0, 19))

    df = pd.DataFrame(linhas)
    return _com_metadados(df)


UFS = [("53", "Distrito Federal"), ("35", "Sao Paulo"), ("31", "Minas Gerais")]

CULTURAS_PAM = list(config.CULTURAS_PAM.items())  # [(codigo, cultura), ...]
CULTURAS_LSPA = list(config.CULTURAS_LSPA.items())

VARIAVEIS_PAM = {"8331": 1000.0, "216": 950.0, "214": 3000.0, "112": 3200.0}
VARIAVEIS_LSPA = {"109": 500.0, "35": 1500.0, "36": 3000.0}


def gerar_pam() -> pd.DataFrame:
    linhas = []
    for uf_codigo, uf_nome in UFS:
        for cultura_codigo, cultura in CULTURAS_PAM:
            for periodo in ("2023", "2024"):
                for variavel, valor_base in VARIAVEIS_PAM.items():
                    linhas.append(
                        {
                            "uf_codigo": uf_codigo,
                            "uf_nome": uf_nome,
                            "cultura": cultura,
                            "cultura_codigo": cultura_codigo,
                            "periodo": periodo,
                            "variavel": variavel,
                            "valor": valor_base + int(periodo) % 100,
                        }
                    )
    df = pd.DataFrame(linhas)
    return _com_metadados(df)


def gerar_lspa() -> pd.DataFrame:
    linhas = []
    for uf_codigo, uf_nome in UFS:
        for cultura_codigo, cultura in CULTURAS_LSPA:
            safra_ciclo = config.CICLO_LSPA.get(cultura_codigo)
            for periodo in ("202601", "202602"):
                for variavel, valor_base in VARIAVEIS_LSPA.items():
                    linhas.append(
                        {
                            "uf_codigo": uf_codigo,
                            "uf_nome": uf_nome,
                            "cultura": cultura,
                            "cultura_codigo": cultura_codigo,
                            "periodo": periodo,
                            "variavel": variavel,
                            "valor": valor_base + int(periodo[-2:]),
                            "safra_ciclo": safra_ciclo,
                        }
                    )
    df = pd.DataFrame(linhas)
    return _com_metadados(df)


def escrever(df: pd.DataFrame, nome: str, particao: str | None = None) -> None:
    destino = config.BRONZE_DIR / nome
    if particao is not None:
        destino = destino / f"ano={particao}"
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / "dados.parquet"
    df.to_parquet(caminho, index=False)
    print(f"gravado {caminho} ({len(df)} linhas)")


def main() -> None:
    escrever(gerar_estacoes(), "estacoes")
    escrever(gerar_clima_horario(), "clima_horario", particao="2026")
    escrever(gerar_pam(), "pam")
    escrever(gerar_lspa(), "lspa")


if __name__ == "__main__":
    main()
