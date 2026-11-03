"""Experimentos da avaliacao: baselines, ablacoes e horizontes.

Todos rodam sobre as mesmas linhas (as safras com o ciclo inteiro observado)
e os mesmos anos de teste, para que as metricas sejam comparaveis entre si.
"""

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from src.ml import features, modelos, validacao


@dataclass(frozen=True)
class Experimento:
    nome: str
    horizonte: int
    fabrica: Callable
    descricao: str


def colunas_do_modelo(horizonte: int, categoricas=True, historico=True, clima=True) -> list[str]:
    colunas = []
    if categoricas:
        colunas += features.COLUNAS_CATEGORICAS
    if historico:
        colunas += features.COLUNAS_HISTORICO
    if clima:
        colunas += features.colunas_clima(horizonte)
    return colunas


def lista() -> list[Experimento]:
    cols = colunas_do_modelo
    lgbm = modelos.LightGBM
    return [
        Experimento("tendencia", 3, modelos.Tendencia,
                    "anomalia zero (segue a reta dos anos anteriores)"),
        Experimento("persistencia", 3, modelos.Persistencia,
                    "repete o rendimento da safra anterior"),
        Experimento("ridge", 3, lambda: modelos.Ridge(cols(3)),
                    "regressao linear, todas as variaveis"),
        Experimento("lgbm_sem_clima", 3, lambda: lgbm(cols(3, clima=False)),
                    "LightGBM so com cultura, UF e anomalia da safra anterior"),
        Experimento("lgbm_so_clima", 3, lambda: lgbm(["cultura"] + cols(3, categoricas=False, historico=False)),
                    "LightGBM so com o clima do ciclo (e a cultura)"),
        Experimento("lgbm_completo", 3, lambda: lgbm(cols(3)),
                    "LightGBM, todas as variaveis"),
        Experimento("lgbm_h1", 1, lambda: lgbm(cols(1)),
                    "LightGBM com o clima do 1o terco do ciclo"),
        Experimento("lgbm_h2", 2, lambda: lgbm(cols(2)),
                    "LightGBM com o clima dos 2 primeiros tercos"),
    ]


MODELO_FINAL = "lgbm_completo"


def tabelas(dados: dict[str, pd.DataFrame]) -> dict[int, pd.DataFrame]:
    """Uma tabela por horizonte, restritas as safras da tabela do ciclo completo."""
    por_h = {h: features.montar_tabela(dados["safra"], dados["clima"], dados["ciclo"], h)
             for h in features.FASES}
    chaves = por_h[3][["uf", "cultura", "ano"]].astype({"uf": str, "cultura": str})
    for h in (1, 2):
        t = por_h[h].astype({"uf": str, "cultura": str}).merge(chaves, on=["uf", "cultura", "ano"])
        for coluna in features.COLUNAS_CATEGORICAS:
            t[coluna] = pd.Categorical(t[coluna], categories=por_h[3][coluna].cat.categories)
        por_h[h] = t
    return por_h


def rodar(dados: dict[str, pd.DataFrame], experimentos: list[Experimento] | None = None,
          min_anos_treino: int = validacao.MIN_ANOS_TREINO) -> dict:
    experimentos = experimentos or lista()
    por_h = tabelas(dados)
    anos = validacao.anos_de_teste(por_h[3], min_anos_treino)
    if not anos:
        raise ValueError("historico curto demais para a validacao temporal")

    previsoes = {
        e.nome: validacao.rolling_origin(por_h[e.horizonte], e.fabrica, anos).assign(modelo=e.nome)
        for e in experimentos
    }
    ref = previsoes["tendencia"]

    linhas, por_cultura = [], []
    for e in experimentos:
        p = previsoes[e.nome]
        m = validacao.metricas(p, ref)
        if e.nome != "tendencia":
            m["skill_ic95"] = validacao.skill_bootstrap(p, ref)
        linhas.append({"experimento": e.nome, "descricao": e.descricao, **m})
        for cultura, pc in p.groupby("cultura", observed=True):
            mc = validacao.metricas(pc, ref[ref["cultura"] == cultura])
            por_cultura.append({"experimento": e.nome, "cultura": cultura, **mc})

    return {
        "tabelas": por_h,
        "anos_teste": anos,
        "previsoes": pd.concat(previsoes.values(), ignore_index=True),
        "metricas": pd.DataFrame(linhas),
        "metricas_cultura": pd.DataFrame(por_cultura),
    }
