"""Figuras, relatorio da avaliacao e model card de uma versao treinada."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.ml import experimentos

COR_DESTAQUE = "#2f6b3a"
COR_NEUTRA = "#9aa59b"


def _fig_skill(metricas: pd.DataFrame, caminho: Path) -> None:
    m = metricas[metricas["experimento"] != "tendencia"].iloc[::-1]
    ic = np.array([list(v) for v in m["skill_ic95"]])
    erro = np.abs(ic.T - m["skill"].to_numpy())
    cores = [COR_DESTAQUE if e == experimentos.MODELO_FINAL else COR_NEUTRA for e in m["experimento"]]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(m["experimento"], m["skill"], xerr=erro, color=cores, capsize=3)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("skill contra a tendencia (1 - MSE / MSE da tendencia)")
    ax.set_title("Validacao temporal, IC 95% por bootstrap de anos")
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def _fig_dispersao(previsoes: pd.DataFrame, caminho: Path) -> None:
    p = previsoes[previsoes["modelo"] == experimentos.MODELO_FINAL]
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    for cultura, g in p.groupby("cultura", observed=True):
        ax.scatter(100 * np.expm1(g["anomalia"]), 100 * np.expm1(g["previsto"]), s=10, alpha=0.6, label=cultura)
    valores = 100 * np.expm1(p[["anomalia", "previsto"]].to_numpy())
    lo, hi = np.nanmin(valores), np.nanmax(valores)
    ax.plot([lo, hi], [lo, hi], color="black", linewidth=0.8)
    ax.set_xlabel("observado: % em relacao a tendencia")
    ax.set_ylabel("previsto: % em relacao a tendencia")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def _fig_importancia(imp: pd.DataFrame, caminho: Path, n: int = 15) -> None:
    top = imp.head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.barh(top["variavel"], top["shap_medio_abs"], color=COR_DESTAQUE)
    ax.set_xlabel("|SHAP| medio (anomalia em log)")
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def _fig_erro_por_ano(previsoes: pd.DataFrame, caminho: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 3.5))
    for modelo in ("tendencia", experimentos.MODELO_FINAL):
        p = previsoes[previsoes["modelo"] == modelo]
        rmse = (p["previsto"] - p["anomalia"]).pow(2).groupby(p["ano"]).mean().pow(0.5)
        ax.plot(rmse.index, rmse.to_numpy(), marker="o", label=modelo)
    ax.set_ylabel("RMSE da anomalia")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def _tabela_md(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    linhas = ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([cab, sep, *linhas])


def _resumo_metricas(metricas: pd.DataFrame) -> pd.DataFrame:
    m = metricas.copy()
    m["skill (IC 95%)"] = [
        "0 (referencia)" if pd.isna(s) or e == "tendencia" else f"{s:.3f} ({ic[0]:.3f} a {ic[1]:.3f})"
        for e, s, ic in zip(m["experimento"], m["skill"], m.get("skill_ic95", [None] * len(m)))
    ]
    m["MAE (kg/ha)"] = m["mae_kg_ha"].round(0).astype(int)
    m["MAPE"] = (100 * m["mape"]).round(1).astype(str) + "%"
    m["recall quebras"] = (100 * m["recall_quebras"]).round(0).fillna(-1).astype(int).astype(str) + "%"
    return m[["experimento", "descricao", "skill (IC 95%)", "MAE (kg/ha)", "MAPE", "recall quebras"]]


def escrever(pasta: Path, resultado: dict, imp: pd.DataFrame, meta: dict) -> None:
    figuras = pasta / "figuras"
    figuras.mkdir(exist_ok=True)
    m = resultado["metricas"]
    _fig_skill(m, figuras / "skill.png")
    _fig_dispersao(resultado["previsoes"], figuras / "previsto_vs_observado.png")
    _fig_importancia(imp, figuras / "importancia.png")
    _fig_erro_por_ano(resultado["previsoes"], figuras / "erro_por_ano.png")

    d = meta["dados"]
    final = meta["metricas"]
    tabela = _tabela_md(_resumo_metricas(m))
    top = ", ".join(imp["variavel"].head(5))
    anos_teste = f"{d['anos_teste'][0]} a {d['anos_teste'][-1]}"

    (pasta / "relatorio.md").write_text(
        f"""# Avaliacao - versao {meta['versao']}

{d['n_safras']} safras ({', '.join(d['culturas'])}) em {len(d['ufs'])} UFs, de {d['anos'][0]} a {d['anos'][1]}.
Validacao temporal com um ano de teste por vez, de {anos_teste}.

{tabela}

Skill: 1 - MSE / MSE da tendencia, na anomalia em log. Recall de quebras: das
safras que ficaram mais de 10% abaixo da tendencia, quantas o modelo previu
pelo menos 5% abaixo.

Variaveis que mais pesam no modelo final (|SHAP| medio): {top}.

![skill](figuras/skill.png)
![previsto vs observado](figuras/previsto_vs_observado.png)
![importancia](figuras/importancia.png)
![erro por ano](figuras/erro_por_ano.png)
""",
        encoding="utf-8",
    )

    (pasta / "README.md").write_text(
        f"""---
language: pt
tags:
  - tabular-regression
  - agriculture
  - climate
  - lightgbm
  - brazil
---

# AgroClima - anomalia de rendimento por clima do ciclo

Preve quanto o rendimento de uma safra (soja, milho, cafe ou cana, por estado
brasileiro) vai ficar acima ou abaixo da tendencia dos anos anteriores, a
partir do clima observado no ciclo da cultura. Codigo, dados e pipeline:
[agroclima-analytics](https://github.com/antoniolaprov/agroclima-analytics).

## Uso pretendido

Estimar a safra ao fim do ciclo, ou ao fim do primeiro ou do segundo terco
(modelos `modelo_h1` e `modelo_h2`), meses antes de o IBGE publicar a PAM. A
unidade e o estado: o modelo nao serve para prever o rendimento de uma fazenda
ou municipio.

## Alvo

`log(rendimento) - tendencia`, em que a tendencia e uma reta ajustada no log
do rendimento dos 15 anos anteriores. O rendimento previsto em kg/ha e
`exp(tendencia + previsao)`.

## Dados

- Rendimento: IBGE, Producao Agricola Municipal (tabela 5457), agregada por UF.
- Clima: estacoes automaticas do INMET, agregadas por UF e mes.
- {d['n_safras']} safras de {d['anos'][0]} a {d['anos'][1]}, {len(d['ufs'])} UFs.

## Variaveis

Por fase do ciclo (tercos): chuva, chuva relativa a normal, temperatura media e
maxima, anomalia de temperatura e dias sem chuva; os mesmos totais no ciclo;
o pior mes em relacao a normal; a anomalia da safra anterior; cultura e UF.
As normais climatologicas usam so anos anteriores.

## Avaliacao

Validacao temporal (rolling origin), um ano de teste por vez, de {anos_teste}.
Referencia: a propria tendencia (anomalia zero).

{tabela}

Skill do modelo final: **{final['skill']:.3f}** (IC 95%, bootstrap de anos:
{final['skill_ic95'][0]:.3f} a {final['skill_ic95'][1]:.3f}).

## Limitacoes

- A amostra e pequena (uma safra por estado e ano) e os anos de teste sao
  poucos; o intervalo de confianca do skill e largo.
- A media estadual da chuva esconde diferencas dentro do estado, e a cobertura
  de estacoes do INMET no comeco dos anos 2000 era bem menor.
- O modelo nao sabe de irrigacao, area plantada, precos ou pragas.
- A tendencia linear se ajusta mal a series que mudaram de patamar (expansao
  de uma cultura para uma regiao nova).

## Versao

`{meta['versao']}` - LightGBM {meta['versoes']['lightgbm']}, scikit-learn {meta['versoes']['scikit-learn']}.
""",
        encoding="utf-8",
    )
