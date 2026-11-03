"""Validacao temporal (rolling origin) e metricas.

Para cada ano de teste Y, o modelo treina com as safras de anos < Y e preve
as de Y. Embaralhar as linhas num k-fold comum colocaria safras de 2020 no
treino de um modelo avaliado em 2015, e o clima de um ano e compartilhado
por todas as UFs vizinhas: o erro medido sairia otimista.
"""

from typing import Callable

import numpy as np
import pandas as pd

MIN_ANOS_TREINO = 5


def anos_de_teste(tabela: pd.DataFrame, min_anos_treino: int = MIN_ANOS_TREINO) -> list[int]:
    anos = sorted(tabela["ano"].unique())
    return [int(a) for a in anos[min_anos_treino:]]


def rolling_origin(tabela: pd.DataFrame, fabrica: Callable, anos_teste: list[int]) -> pd.DataFrame:
    """Previsoes fora da amostra de um modelo, um ano de teste por vez.

    fabrica() devolve um modelo novo a cada ano, para nada passar de um ajuste
    para o outro.
    """
    partes = []
    for ano in anos_teste:
        treino = tabela[tabela["ano"] < ano]
        teste = tabela[tabela["ano"] == ano]
        if treino.empty or teste.empty:
            continue
        modelo = fabrica().fit(treino, treino["anomalia"].to_numpy())
        partes.append(
            teste[["uf", "cultura", "ano", "rendimento", "tendencia_log", "anomalia"]]
            .assign(modelo=modelo.nome, previsto=modelo.predict(teste))
        )
    previsoes = pd.concat(partes, ignore_index=True)
    previsoes["rendimento_previsto"] = np.exp(previsoes["tendencia_log"] + previsoes["previsto"])
    return previsoes


def metricas(previsoes: pd.DataFrame, referencia: pd.DataFrame | None = None) -> dict:
    """Erros de uma serie de previsoes. Com referencia (as previsoes da
    tendencia nas mesmas linhas), inclui o skill: 1 - MSE / MSE da referencia."""
    erro = previsoes["previsto"] - previsoes["anomalia"]
    erro_kg = previsoes["rendimento_previsto"] - previsoes["rendimento"]
    saida = {
        "n": int(len(previsoes)),
        "rmse_anomalia": float(np.sqrt(np.mean(erro**2))),
        "mae_kg_ha": float(np.mean(np.abs(erro_kg))),
        "mape": float(np.mean(np.abs(erro_kg) / previsoes["rendimento"])),
    }
    if previsoes["previsto"].std() > 0:
        saida["corr_anomalia"] = float(np.corrcoef(previsoes["previsto"], previsoes["anomalia"])[0, 1])
    if referencia is not None:
        chave = ["uf", "cultura", "ano"]
        juntos = previsoes[chave + ["previsto", "anomalia"]].merge(
            referencia[chave + ["previsto"]], on=chave, suffixes=("", "_ref")
        )
        e2 = (juntos["previsto"] - juntos["anomalia"]) ** 2
        e2_ref = (juntos["previsto_ref"] - juntos["anomalia"]) ** 2
        saida["skill"] = float(1 - e2.mean() / e2_ref.mean())

    # Quebras: safras que ficaram mais de 10% abaixo da tendencia. E o caso
    # que importa para quem usa a previsao, e o mais raro.
    quebra = previsoes["anomalia"] < np.log(0.9)
    if quebra.any():
        saida["n_quebras"] = int(quebra.sum())
        saida["recall_quebras"] = float((previsoes.loc[quebra, "previsto"] < np.log(0.95)).mean())
    return saida


def skill_bootstrap(previsoes: pd.DataFrame, referencia: pd.DataFrame, n: int = 2000,
                    semente: int = 0) -> tuple[float, float]:
    """Intervalo de 95% do skill, reamostrando anos inteiros.

    Reamostrar linhas soltas ignoraria que as safras de um mesmo ano tem erros
    correlacionados (o mesmo El Nino afeta varias UFs) e daria um intervalo
    estreito demais.
    """
    chave = ["uf", "cultura", "ano"]
    juntos = previsoes.merge(referencia[chave + ["previsto"]], on=chave, suffixes=("", "_ref"))
    juntos["e2"] = (juntos["previsto"] - juntos["anomalia"]) ** 2
    juntos["e2_ref"] = (juntos["previsto_ref"] - juntos["anomalia"]) ** 2
    por_ano = juntos.groupby("ano")[["e2", "e2_ref"]].sum()

    rng = np.random.default_rng(semente)
    sorteios = rng.integers(0, len(por_ano), size=(n, len(por_ano)))
    e2 = por_ano["e2"].to_numpy()[sorteios].sum(axis=1)
    e2_ref = por_ano["e2_ref"].to_numpy()[sorteios].sum(axis=1)
    skills = 1 - e2 / e2_ref
    return float(np.percentile(skills, 2.5)), float(np.percentile(skills, 97.5))
