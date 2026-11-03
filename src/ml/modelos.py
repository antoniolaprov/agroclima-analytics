"""Modelos comparados. Todos preveem a anomalia (log), nao o rendimento.

- tendencia: anomalia zero, ou seja, a safra segue a reta dos anos anteriores.
  E a referencia do skill: um modelo so ajuda se errar menos que ela.
- persistencia: repete o rendimento da safra anterior.
- ridge: regressao linear regularizada, para saber quanto do sinal e linear.
- lightgbm: arvores com gradient boosting.

Os hiperparametros do LightGBM sao fixos e conservadores (arvores rasas,
muitas amostras por folha). Com cerca de dois mil exemplos, ajustar
hiperparametros dentro da validacao temporal tenderia a sobreajustar a
propria validacao.
"""

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.ml.features import COLUNAS_CATEGORICAS

PARAMS_LGBM = {
    "objective": "huber",
    "alpha": 0.15,
    "n_estimators": 400,
    "learning_rate": 0.03,
    "num_leaves": 15,
    "max_depth": 4,
    "min_child_samples": 25,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "verbose": -1,
}


class Tendencia:
    nome = "tendencia"

    def fit(self, X, y):
        return self

    def predict(self, X):
        return np.zeros(len(X))


class Persistencia:
    nome = "persistencia"

    def fit(self, X, y):
        return self

    def predict(self, X):
        anomalia = np.log(X["rendimento_anterior"].to_numpy(dtype=float)) - X["tendencia_log"].to_numpy()
        return np.nan_to_num(anomalia, nan=0.0)


class Ridge:
    nome = "ridge"

    def __init__(self, colunas: list[str]):
        self.colunas = colunas
        numericas = [c for c in colunas if c not in COLUNAS_CATEGORICAS]
        categoricas = [c for c in colunas if c in COLUNAS_CATEGORICAS]
        # keep_empty_features: nos primeiros anos as normais ainda nao existem e
        # colunas como chuva_rel_f1 chegam inteiras nulas no treino.
        imputacao = SimpleImputer(strategy="median", keep_empty_features=True)
        preparo = ColumnTransformer(
            [
                ("num", make_pipeline(imputacao, StandardScaler()), numericas),
                ("cat", OneHotEncoder(handle_unknown="ignore"), categoricas),
            ]
        )
        self.pipeline = make_pipeline(preparo, RidgeCV(alphas=np.logspace(-2, 3, 20)))

    def fit(self, X, y):
        self.pipeline.fit(X[self.colunas], y)
        return self

    def predict(self, X):
        return self.pipeline.predict(X[self.colunas])


class LightGBM:
    nome = "lightgbm"

    def __init__(self, colunas: list[str], params: dict | None = None, semente: int = 42):
        self.colunas = colunas
        self.params = {**PARAMS_LGBM, **(params or {}), "random_state": semente}
        self.modelo = lgb.LGBMRegressor(**self.params)

    def fit(self, X, y):
        self.modelo.fit(X[self.colunas], y)
        return self

    def predict(self, X):
        return self.modelo.predict(X[self.colunas])

    def contribuicoes(self, X) -> pd.DataFrame:
        """Contribuicao de cada variavel para cada previsao (valores SHAP do TreeSHAP do LightGBM)."""
        valores = self.modelo.predict(X[self.colunas], pred_contrib=True)
        return pd.DataFrame(valores[:, :-1], columns=self.colunas, index=X.index)
