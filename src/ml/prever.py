"""Previsao das safras que o IBGE ainda nao publicou.

Para cada estado e cultura, olha os anos de safra depois do ultimo ano da PAM
e usa o maior horizonte que o clima ja observado permite: no meio do ciclo da
soja, por exemplo, so o modelo de horizonte 1 ou 2 tem o que precisa.

Uso: python -m src.ml.prever [--duckdb CAMINHO] [--modelo DIR]
"""

import argparse
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.ml import alvo, features
from src.ml import dados as dados_ml
from src.ml.treino import MODELOS_DIR

log = logging.getLogger(__name__)


def _safras_pendentes(safra: pd.DataFrame, clima: pd.DataFrame, ciclo: pd.DataFrame) -> pd.DataFrame:
    candidatas = features.clima_da_safra(clima, ciclo, horizonte=1)[["uf", "cultura", "ano"]]
    ultimo = safra.groupby(["uf", "cultura"])["ano"].max().rename("ultimo_ano").reset_index()
    pendentes = candidatas.merge(ultimo, on=["uf", "cultura"])
    return pendentes.loc[pendentes["ano"] > pendentes["ultimo_ano"], ["uf", "cultura", "ano"]]


def prever(dados: dict[str, pd.DataFrame], pasta_modelo: Path) -> pd.DataFrame:
    safra, clima, ciclo = dados["safra"], dados["clima"], dados["ciclo"]
    pendentes = _safras_pendentes(safra, clima, ciclo)
    colunas = ["uf", "cultura", "ano", "horizonte", "anomalia_prevista_pct",
               "rendimento_tendencia", "rendimento_previsto"]
    if pendentes.empty:
        return pd.DataFrame(columns=colunas)

    estendida = pd.concat([safra, pendentes.assign(rendimento=np.nan)], ignore_index=True)
    base = alvo.calcular(estendida).merge(pendentes, on=["uf", "cultura", "ano"])
    base = base[base["tendencia_log"].notna()]

    partes = []
    for h in features.FASES:
        caminho = pasta_modelo / f"modelo_h{h}.joblib"
        if not caminho.exists():
            continue
        modelo = joblib.load(caminho)
        tabela = base.merge(features.clima_da_safra(clima, ciclo, h), on=["uf", "cultura", "ano"])
        if tabela.empty:
            continue
        for coluna in features.COLUNAS_CATEGORICAS:
            tabela[coluna] = tabela[coluna].astype("category")
        partes.append(tabela.assign(horizonte=h, previsto=modelo.predict(tabela)))

    if not partes:
        return pd.DataFrame(columns=colunas)

    todas = pd.concat(partes, ignore_index=True).astype({"uf": str, "cultura": str})
    # Fica a previsao com mais clima observado de cada safra.
    melhor = todas.sort_values("horizonte").groupby(["uf", "cultura", "ano"]).tail(1)
    melhor = melhor.assign(
        anomalia_prevista_pct=100 * np.expm1(melhor["previsto"]),
        rendimento_tendencia=np.exp(melhor["tendencia_log"]),
        rendimento_previsto=np.exp(melhor["tendencia_log"] + melhor["previsto"]),
    )
    return melhor[colunas].sort_values(["cultura", "uf", "ano"]).reset_index(drop=True)


def main(caminho_duckdb: Path | None = None, pasta_modelo: Path = MODELOS_DIR / "atual") -> int:
    if not pasta_modelo.exists():
        raise FileNotFoundError(f"nenhum modelo em {pasta_modelo}; rode python -m src.ml.treino antes")
    previsoes = prever(dados_ml.carregar(caminho_duckdb), pasta_modelo)
    destino = pasta_modelo.parent / "previsoes.csv"
    previsoes.round(1).to_csv(destino, index=False)
    log.info("%d previsoes gravadas em %s", len(previsoes), destino)
    return len(previsoes)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--duckdb", type=Path, default=None)
    p.add_argument("--modelo", type=Path, default=MODELOS_DIR / "atual")
    a = p.parse_args()
    main(a.duckdb, a.modelo)
