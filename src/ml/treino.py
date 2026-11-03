"""Avalia os experimentos, treina o modelo final e decide se ele substitui o atual.

Uso: python -m src.ml.treino [--duckdb CAMINHO] [--saida DIR] [--sem-mlflow] [--forcar]

Cada execucao grava uma versao em data/modelos/<versao>/. Ela so vira
data/modelos/atual/ se o skill da validacao temporal nao piorar mais que
TOLERANCIA em relacao a versao atual: um dado novo do IBGE com problema, ou
uma mudanca no codigo, nao troca silenciosamente um modelo bom por um pior.

O Airflow chama o treino todo dia, mas o IBGE publica a PAM uma vez por ano
e o INMET atualiza o zip do ano corrente uma vez por mes. Se as tabelas de
entrada nao mudaram desde a versao atual, o treino nao roda (--forcar ignora
essa checagem).
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
import lightgbm
import numpy as np
import pandas as pd
import sklearn

from src import config
from src.ml import alvo, experimentos, modelos, relatorio
from src.ml import dados as dados_ml

log = logging.getLogger(__name__)

MODELOS_DIR = config.DATA_DIR / "modelos"
MLFLOW_DIR = config.DATA_DIR / "mlruns"
NOME_EXPERIMENTO_MLFLOW = "agroclima-anomalia-rendimento"
TOLERANCIA = 0.02


def treinar_finais(tabelas: dict[int, pd.DataFrame]) -> dict[int, modelos.LightGBM]:
    finais = {}
    for h, tabela in tabelas.items():
        m = modelos.LightGBM(experimentos.colunas_do_modelo(h))
        finais[h] = m.fit(tabela, tabela["anomalia"].to_numpy())
    return finais


def importancia(modelo: modelos.LightGBM, tabela: pd.DataFrame) -> pd.DataFrame:
    contrib = modelo.contribuicoes(tabela)
    return (
        contrib.abs().mean().rename("shap_medio_abs").sort_values(ascending=False)
        .rename_axis("variavel").reset_index()
    )


def assinatura(dados: dict[str, pd.DataFrame]) -> str:
    """Hash das tabelas de entrada, independente da ordem das linhas."""
    partes = []
    for nome in sorted(dados):
        df = dados[nome]
        df = df[sorted(df.columns)].sort_values(sorted(df.columns)).reset_index(drop=True)
        partes.append(f"{nome}:{pd.util.hash_pandas_object(df, index=False).sum()}")
    return hashlib.sha256("|".join(partes).encode()).hexdigest()[:16]


def metadados_atual(destino: Path) -> dict | None:
    meta = destino / "atual" / "metadados.json"
    if not meta.exists():
        return None
    return json.loads(meta.read_text(encoding="utf-8"))


def decidir_promocao(skill_novo: float, skill_anterior: float | None,
                     tolerancia: float = TOLERANCIA) -> bool:
    return skill_anterior is None or skill_novo >= skill_anterior - tolerancia


def _metricas_do_final(resultado: dict) -> dict:
    linha = resultado["metricas"].set_index("experimento").loc[experimentos.MODELO_FINAL]
    saida = {}
    for chave, valor in linha.drop("descricao").items():
        if isinstance(valor, np.generic):
            valor = valor.item()
        if isinstance(valor, float) and np.isnan(valor):
            continue
        saida[chave] = valor
    saida["skill_ic95"] = list(saida["skill_ic95"])
    return saida


def _registrar_mlflow(resultado: dict, pasta: Path, versao: str) -> str | None:
    try:
        import mlflow
    except ImportError:
        log.info("mlflow nao instalado, tracking ignorado")
        return None

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", MLFLOW_DIR.resolve().as_uri()))
    mlflow.set_experiment(NOME_EXPERIMENTO_MLFLOW)
    with mlflow.start_run(run_name=versao) as pai:
        mlflow.log_params(
            {
                "anos_teste": f"{resultado['anos_teste'][0]}-{resultado['anos_teste'][-1]}",
                "n_safras": len(resultado["tabelas"][3]),
                "janela_tendencia": alvo.JANELA_ANOS,
            }
        )
        for linha in resultado["metricas"].to_dict("records"):
            with mlflow.start_run(run_name=linha["experimento"], nested=True):
                mlflow.set_tag("descricao", linha["descricao"])
                for chave, valor in linha.items():
                    if chave == "skill_ic95" and isinstance(valor, tuple):
                        mlflow.log_metrics({"skill_ic95_inf": valor[0], "skill_ic95_sup": valor[1]})
                    elif isinstance(valor, (int, float)) and not np.isnan(valor):
                        mlflow.log_metric(chave, valor)
        mlflow.log_params({f"lgbm_{k}": v for k, v in modelos.PARAMS_LGBM.items()})
        mlflow.log_artifacts(str(pasta))
        return pai.info.run_id


def main(caminho_duckdb: Path | None = None, destino: Path = MODELOS_DIR,
         usar_mlflow: bool = True, dados: dict | None = None, forcar: bool = False) -> dict:
    dados = dados or dados_ml.carregar(caminho_duckdb)
    hash_dados = assinatura(dados)
    atual = metadados_atual(destino)
    if atual and atual.get("hash_dados") == hash_dados and not forcar:
        log.info("dados iguais aos da versao %s, treino nao necessario", atual["versao"])
        return {"versao": atual["versao"], "promovido": False, "treinado": False,
                "skill": atual["metricas"]["skill"]}

    resultado = experimentos.rodar(dados)
    tabelas = resultado["tabelas"]

    versao = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pasta = destino / versao
    pasta.mkdir(parents=True, exist_ok=True)

    finais = treinar_finais(tabelas)
    for h, modelo in finais.items():
        joblib.dump(modelo, pasta / f"modelo_h{h}.joblib")

    imp = importancia(finais[3], tabelas[3])
    imp.to_csv(pasta / "importancia.csv", index=False)
    resultado["metricas"].to_csv(pasta / "metricas.csv", index=False)
    resultado["metricas_cultura"].to_csv(pasta / "metricas_cultura.csv", index=False)
    resultado["previsoes"].to_csv(pasta / "previsoes_backtest.csv", index=False)

    metricas_final = _metricas_do_final(resultado)
    t3 = tabelas[3]
    metadados = {
        "versao": versao,
        "modelo": experimentos.MODELO_FINAL,
        "alvo": "log(rendimento) - tendencia linear dos 15 anos anteriores",
        "variaveis": {h: experimentos.colunas_do_modelo(h) for h in finais},
        "params_lightgbm": modelos.PARAMS_LGBM,
        "dados": {
            "n_safras": int(len(t3)),
            "anos": [int(t3["ano"].min()), int(t3["ano"].max())],
            "culturas": sorted(t3["cultura"].astype(str).unique()),
            "ufs": sorted(t3["uf"].astype(str).unique()),
            "anos_teste": resultado["anos_teste"],
        },
        "metricas": metricas_final,
        "hash_dados": hash_dados,
        "versoes": {"lightgbm": lightgbm.__version__, "scikit-learn": sklearn.__version__,
                    "pandas": pd.__version__},
    }

    anterior = atual["metricas"]["skill"] if atual else None
    promovido = decidir_promocao(metricas_final["skill"], anterior)
    metadados["promocao"] = {"promovido": promovido, "skill_anterior": anterior, "tolerancia": TOLERANCIA}

    relatorio.escrever(pasta, resultado, imp, metadados)
    if usar_mlflow:
        metadados["mlflow_run_id"] = _registrar_mlflow(resultado, pasta, versao)
    (pasta / "metadados.json").write_text(json.dumps(metadados, indent=2, ensure_ascii=False), encoding="utf-8")

    if promovido:
        shutil.rmtree(destino / "atual", ignore_errors=True)
        shutil.copytree(pasta, destino / "atual")
        log.info("versao %s promovida (skill %.3f, anterior %s)", versao, metricas_final["skill"], anterior)
    else:
        log.warning("versao %s nao promovida: skill %.3f contra %.3f da atual",
                    versao, metricas_final["skill"], anterior)

    return {"versao": versao, "promovido": promovido, "treinado": True,
            "skill": metricas_final["skill"], "skill_ic95": metricas_final["skill_ic95"]}


def _args():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--duckdb", type=Path, default=None)
    p.add_argument("--saida", type=Path, default=MODELOS_DIR)
    p.add_argument("--sem-mlflow", action="store_true")
    p.add_argument("--forcar", action="store_true", help="treina mesmo sem dado novo")
    return p.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    a = _args()
    print(json.dumps(main(a.duckdb, a.saida, not a.sem_mlflow, forcar=a.forcar), indent=2))
