"""Alvo do modelo: o quanto o rendimento de uma safra fugiu da tendencia.

O rendimento das culturas sobe ano a ano com tecnologia e manejo; soja em MT
rende hoje quase o dobro do que rendia nos anos 90. Prever o rendimento cru
seria, na maior parte, prever essa tendencia, e o clima mal apareceria. Por
isso o alvo e a anomalia: log(rendimento) menos a tendencia esperada para o
ano.

A tendencia de cada ano e ajustada so com os anos anteriores (janela movel).
Ajustar uma reta na serie inteira e subtrair, o jeito mais comum, usa o
futuro: o rendimento de 2025 entra no calculo da anomalia de 2010, e a
validacao temporal deixa de valer.
"""

import numpy as np
import pandas as pd

JANELA_ANOS = 15
MIN_ANOS = 8


def tendencia_passada(anos: np.ndarray, log_rend: np.ndarray, janela: int = JANELA_ANOS,
                      min_anos: int = MIN_ANOS) -> np.ndarray:
    """Para cada ano t, a reta ajustada nos anos [t - janela, t - 1], avaliada em t.

    Anos com log_rend nulo (safra ainda nao publicada) recebem a tendencia mas
    nao entram no ajuste.
    """
    previsto = np.full(len(anos), np.nan)
    for i, ano in enumerate(anos):
        mascara = (anos < ano) & (anos >= ano - janela) & ~np.isnan(log_rend)
        if mascara.sum() < min_anos:
            continue
        inclinacao, intercepto = np.polyfit(anos[mascara], log_rend[mascara], 1)
        previsto[i] = intercepto + inclinacao * ano
    return previsto


def calcular(safra: pd.DataFrame, janela: int = JANELA_ANOS, min_anos: int = MIN_ANOS) -> pd.DataFrame:
    """Acrescenta tendencia_log, anomalia e as colunas da safra anterior.

    Linhas sem historico suficiente para a tendencia ficam com anomalia nula.
    """
    partes = []
    for _, grupo in safra.sort_values("ano").groupby(["uf", "cultura"], sort=False):
        g = grupo.copy()
        anos = g["ano"].to_numpy(dtype=float)
        log_rend = np.log(g["rendimento"].to_numpy(dtype=float))
        g["log_rendimento"] = log_rend
        g["tendencia_log"] = tendencia_passada(anos, log_rend, janela, min_anos)
        g["anomalia"] = g["log_rendimento"] - g["tendencia_log"]

        # Safra anterior so quando e o ano imediatamente anterior; a PAM tem
        # buracos em algumas series.
        adjacente = g["ano"].diff() == 1
        g["rendimento_anterior"] = g["rendimento"].shift(1).where(adjacente)
        g["anomalia_anterior"] = g["anomalia"].shift(1).where(adjacente)
        partes.append(g)
    return pd.concat(partes, ignore_index=True)
