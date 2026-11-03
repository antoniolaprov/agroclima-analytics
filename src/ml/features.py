"""Variaveis de clima de cada safra, por fase do ciclo.

O ciclo de cada cultura (seed ciclo_cultura do dbt) e dividido em tres fases
de mesmo tamanho: para soja, de outubro a marco, a fase 1 e out-nov
(plantio), a 2 e dez-jan (floracao e enchimento de graos) e a 3 e fev-mar
(colheita). Uma seca na fase 2 pesa muito mais que a mesma seca na fase 3, e
a chuva total do ciclo nao enxerga essa diferenca.

O horizonte diz quantas fases ja foram observadas quando a previsao e feita:
horizonte 1 preve a safra com o clima so do primeiro terco do ciclo.

As normais climatologicas (chuva e temperatura esperadas para a UF naquele
mes) usam so os anos anteriores ao mes em questao. As anomalias da tabela
gold_clima_uf_mensal usam o periodo inteiro e por isso nao entram aqui.
"""

import numpy as np
import pandas as pd

from src.ml import alvo

FASES = (1, 2, 3)
MIN_ANOS_NORMAL = 5

COLUNAS_CATEGORICAS = ["cultura", "uf"]
COLUNAS_HISTORICO = ["anomalia_anterior"]


def meses_do_ciclo(ciclo: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por cultura e mes do ciclo, com a posicao, a fase e o deslocamento do ano."""
    linhas = []
    for c in ciclo.itertuples(index=False):
        n = (c.mes_fim - c.mes_inicio) % 12 + 1
        for pos in range(n):
            mes = (c.mes_inicio - 1 + pos) % 12 + 1
            linhas.append(
                {
                    "cultura": c.cultura,
                    "mes": mes,
                    "posicao": pos,
                    "meses_ciclo": n,
                    "fase": pos * len(FASES) // n + 1,
                    # Mes do ano civil anterior ao da colheita (out-dez da soja
                    # 2024/25 pertence a safra 2025).
                    "desloca_ano": int(c.mes_inicio > c.mes_fim and mes >= c.mes_inicio),
                }
            )
    return pd.DataFrame(linhas)


def com_normais(clima: pd.DataFrame, min_anos: int = MIN_ANOS_NORMAL) -> pd.DataFrame:
    """Acrescenta chuva e temperatura normais da UF no mes, so com anos anteriores."""
    df = clima.sort_values(["uf", "mes", "ano"]).copy()
    grupos = df.groupby(["uf", "mes"], sort=False)
    for coluna, nova in (("precipitacao", "precip_normal"), ("temp_media", "temp_normal")):
        df[nova] = grupos[coluna].transform(
            lambda s: s.shift(1).expanding(min_periods=min_anos).mean()
        )
    return df


def _soma_ou_nulo(serie: pd.Series) -> float:
    return serie.sum() if serie.notna().all() else np.nan


def _agregar(g: pd.DataFrame) -> dict:
    return {
        "chuva": g["precipitacao"].sum(),
        "chuva_rel": g["precipitacao"].sum() / _soma_ou_nulo(g["precip_normal"]) - 1,
        "temp": g["temp_media"].mean(),
        "anom_temp": (g["temp_media"] - g["temp_normal"]).mean(),
        "tmax": g["temp_max"].mean(),
        "secos": g["dias_sem_chuva"].sum(),
    }


def clima_da_safra(clima: pd.DataFrame, ciclo: pd.DataFrame, horizonte: int = 3) -> pd.DataFrame:
    """Uma linha por uf, cultura e ano de safra com as variaveis das fases observadas.

    Safras com algum mes sem chuva medida na janela sao descartadas, pela mesma
    razao do gold_clima_safra: um total parcial pareceria seca.
    """
    if horizonte not in FASES:
        raise ValueError(f"horizonte deve ser 1, 2 ou 3, nao {horizonte}")

    meses = meses_do_ciclo(ciclo)
    meses = meses[meses["fase"] <= horizonte]
    esperados = meses.groupby("cultura")["mes"].count().rename("esperados")

    df = com_normais(clima).merge(meses, on="mes")
    df["ano_safra"] = df["ano"] + df["desloca_ano"]
    df["precip_rel_mes"] = df["precipitacao"] / df["precip_normal"] - 1

    chave = ["uf", "cultura", "ano_safra"]
    completos = (
        df.groupby(chave)["precipitacao"].count().rename("observados").reset_index()
        .merge(esperados, on="cultura")
    )
    completos = completos.loc[completos["observados"] == completos["esperados"], chave]
    df = df.merge(completos, on=chave)

    linhas = []
    for (uf, cultura, ano), g in df.groupby(chave, sort=False):
        linha = {"uf": uf, "cultura": cultura, "ano": ano}
        for fase, gf in g.groupby("fase"):
            for nome, valor in _agregar(gf).items():
                linha[f"{nome}_f{fase}"] = valor
        for nome, valor in _agregar(g).items():
            linha[f"{nome}_total"] = valor
        # Pior mes da janela em relacao ao normal: pega veranicos que a soma
        # do ciclo dilui.
        linha["pior_mes_rel"] = g["precip_rel_mes"].min()
        linha["n_estacoes_min"] = g["n_estacoes"].min()
        linhas.append(linha)
    if not linhas:
        return pd.DataFrame(columns=["uf", "cultura", "ano", *colunas_clima(horizonte)])
    return pd.DataFrame(linhas)


def colunas_clima(horizonte: int) -> list[str]:
    nomes = ["chuva", "chuva_rel", "temp", "anom_temp", "tmax", "secos"]
    colunas = [f"{n}_f{f}" for f in range(1, horizonte + 1) for n in nomes]
    return colunas + [f"{n}_total" for n in nomes] + ["pior_mes_rel"]


def montar_tabela(safra: pd.DataFrame, clima: pd.DataFrame, ciclo: pd.DataFrame,
                  horizonte: int = 3) -> pd.DataFrame:
    """Tabela de modelagem: alvo, tendencia e variaveis, so linhas com alvo definido."""
    com_alvo = alvo.calcular(safra)
    tabela = com_alvo.merge(clima_da_safra(clima, ciclo, horizonte), on=["uf", "cultura", "ano"])
    tabela = tabela[tabela["anomalia"].notna()].reset_index(drop=True)
    for coluna in COLUNAS_CATEGORICAS:
        tabela[coluna] = tabela[coluna].astype("category")
    return tabela
