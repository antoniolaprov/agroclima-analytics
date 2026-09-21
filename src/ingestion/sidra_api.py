import pandas as pd

from src import config
from src.ingestion import base

AUSENTES = {"...", "-", "..", "X"}

VARIAVEIS_PAM = ["8331", "216", "214", "112", "215"]
VARIAVEIS_LSPA = ["109", "216", "35", "36"]


def _para_float(valor: str) -> float:
    if valor is None or str(valor).strip() in AUSENTES:
        return float("nan")
    return float(valor)


def montar_url(tabela: str, periodos: str, variaveis: list[str], classificacao: str, categorias: list[str]) -> str:
    return (
        f"{config.SIDRA_BASE}/{tabela}/periodos/{periodos}"
        f"/variaveis/{'|'.join(variaveis)}"
        f"?localidades=N3[all]&classificacao={classificacao}[{','.join(categorias)}]"
    )


def parse_resposta(payload: list, mapa_culturas: dict) -> pd.DataFrame:
    linhas = []
    for bloco in payload:
        variavel = bloco["id"]
        for resultado in bloco["resultados"]:
            categoria = resultado["classificacoes"][0]["categoria"]
            codigo = next(iter(categoria))
            cultura = mapa_culturas.get(codigo)
            if cultura is None:
                continue
            for serie in resultado["series"]:
                for periodo, valor in serie["serie"].items():
                    linhas.append(
                        {
                            "uf_codigo": serie["localidade"]["id"],
                            "uf_nome": serie["localidade"]["nome"],
                            "cultura": cultura,
                            "cultura_codigo": codigo,
                            "periodo": periodo,
                            "variavel": variavel,
                            "valor": _para_float(valor),
                        }
                    )
    return pd.DataFrame(linhas)


def ingest_pam() -> int:
    url = montar_url("5457", "all", VARIAVEIS_PAM, "782", list(config.CULTURAS_PAM))
    df = parse_resposta(base.http_get(url, timeout=180).json(), config.CULTURAS_PAM)
    base.write_parquet(df, "pam", url)
    return len(df)


def ingest_lspa() -> int:
    # A serie completa da LSPA passa do limite de valores por consulta do SIDRA,
    # que responde 500. Ela so e usada nos anos da janela do clima, entao a
    # consulta fica restrita a esses meses.
    periodos = f"{min(config.ANOS_CLIMA)}01-{max(config.ANOS_CLIMA)}12"
    url = montar_url("6588", periodos, VARIAVEIS_LSPA, "48", list(config.CULTURAS_LSPA))
    df = parse_resposta(base.http_get(url, timeout=180).json(), config.CULTURAS_LSPA)
    df["safra_ciclo"] = df["cultura_codigo"].map(config.CICLO_LSPA)
    base.write_parquet(df, "lspa", url)
    return len(df)
