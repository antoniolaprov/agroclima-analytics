import plotly.express as px
import streamlit as st

from dashboard import data, graficos
from dashboard.views.overview import malha_ufs

HORIZONTES = {1: "1/3 do ciclo observado", 2: "2/3 do ciclo observado", 3: "ciclo completo"}

# Mesmos codigos do dim_uf do dbt; a malha do mapa e indexada por eles.
CODIGO_UF = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17",
    "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27",
    "SE": "28", "BA": "29", "MG": "31", "ES": "32", "RJ": "33", "SP": "35", "PR": "41",
    "SC": "42", "RS": "43", "MS": "50", "MT": "51", "GO": "52", "DF": "53",
}

# Vermelho abaixo da tendencia, verde acima. O meio fica no zero.
ESCALA = ["#c0392b", "#f3e9d2", "#2e8b57"]


def _rotulo_safra(ano: int, horizonte: int) -> str:
    return f"Safra {ano} ({HORIZONTES[horizonte]})"


def _sem_modelo():
    st.info(
        "Nenhuma previsao gerada ainda. Rode o treino e a previsao depois do pipeline:\n\n"
        "```\npython -m src.ml.treino\npython -m src.ml.prever\n```"
    )


def render(filtros):
    st.header("Previsao de safra")

    df = data.previsoes()
    modelo = data.modelo_atual()
    if df.empty or modelo is None:
        _sem_modelo()
        return

    culturas = [c for c in filtros["culturas"] if c in set(df["cultura"])]
    if not culturas:
        st.info("O modelo nao tem previsao pendente para as culturas selecionadas.")
        return
    cultura = culturas[0]
    if len(culturas) > 1:
        cultura = st.selectbox("Cultura", culturas)

    df = df[df["cultura"] == cultura]
    # Pode haver mais de uma safra pendente: a de 2026 com o ciclo inteiro e a
    # 2026/27 so com o comeco do ciclo, por exemplo.
    safras = df.groupby("ano")["horizonte"].max().sort_index()
    if len(safras) > 1:
        ano = st.radio(
            "Safra", list(safras.index), horizontal=True,
            format_func=lambda a: _rotulo_safra(a, int(safras[a])),
        )
    else:
        ano = int(safras.index[0])
    df = df[df["ano"] == ano]

    metricas = modelo["metricas"]
    ic = metricas.get("skill_ic95", [None, None])
    st.caption(
        f"{cultura.capitalize()}, {_rotulo_safra(ano, int(df['horizonte'].max())).lower()}. "
        f"Quanto o rendimento deve ficar acima ou abaixo da tendencia dos 15 anos anteriores, "
        f"pelo clima observado no ciclo. O IBGE so publica o numero oficial em setembro do ano seguinte."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Skill na validacao", graficos.numero(metricas["skill"], casas=2),
                help="1 - MSE / MSE da tendencia. Zero empata com supor que a safra segue a reta.")
    if ic[0] is not None:
        col2.metric("IC 95% do skill", f"{graficos.numero(ic[0], casas=2)} a {graficos.numero(ic[1], casas=2)}")
    col3.metric("Erro medio (kg/ha)", graficos.numero(metricas["mae_kg_ha"]))

    if metricas["skill"] <= 0:
        st.warning(
            "Na validacao temporal o modelo nao ganhou da tendencia. Trate estas previsoes "
            "como a tendencia ajustada, nao como um sinal do clima."
        )

    limite = max(abs(df["anomalia_prevista_pct"]).max(), 5)
    st.subheader(f"Anomalia prevista por UF ({len(df)} UFs com clima completo)")
    fig = px.choropleth(
        df.assign(uf_codigo=df["uf"].map(CODIGO_UF)),
        geojson=malha_ufs(),
        locations="uf_codigo",
        featureidkey="properties.codarea",
        color="anomalia_prevista_pct",
        color_continuous_scale=ESCALA,
        range_color=(-limite, limite),
        hover_name="uf",
        hover_data={"uf_codigo": False, "anomalia_prevista_pct": ":+.1f",
                    "rendimento_previsto": ":,.0f", "rendimento_tendencia": ":,.0f"},
        labels={"anomalia_prevista_pct": "Anomalia (%)", "rendimento_previsto": "Previsto (kg/ha)",
                "rendimento_tendencia": "Tendencia (kg/ha)"},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, height=520, separators=",.")
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})

    selecionadas = df[df["uf"].isin(filtros["ufs"])].sort_values("anomalia_prevista_pct")
    if not selecionadas.empty:
        st.subheader("UFs selecionadas")
        fig = px.bar(
            selecionadas.assign(sinal=selecionadas["anomalia_prevista_pct"].ge(0).map(
                {True: "acima da tendencia", False: "abaixo da tendencia"})),
            x="anomalia_prevista_pct", y="uf", orientation="h", color="sinal",
            color_discrete_map={"acima da tendencia": ESCALA[2], "abaixo da tendencia": ESCALA[0]},
            hover_data={"rendimento_previsto": ":,.0f", "rendimento_tendencia": ":,.0f", "sinal": False},
            labels={"anomalia_prevista_pct": "Anomalia prevista (%)", "uf": "",
                    "rendimento_previsto": "Previsto (kg/ha)", "rendimento_tendencia": "Tendencia (kg/ha)"},
        )
        fig.add_vline(x=0, line_color=graficos.COR_REFERENCIA, line_width=1)
        st.plotly_chart(graficos.estilo(fig, legenda=False), use_container_width=True)

    with st.expander("Ver tabela"):
        st.dataframe(
            df.sort_values("anomalia_prevista_pct")[
                ["uf", "anomalia_prevista_pct", "rendimento_previsto", "rendimento_tendencia", "horizonte"]
            ],
            hide_index=True,
        )

    with st.expander("Como o modelo foi avaliado"):
        st.markdown(
            f"Versao `{modelo['versao']}`, LightGBM. Validacao temporal com um ano de teste por vez "
            f"({modelo['dados']['anos_teste'][0]} a {modelo['dados']['anos_teste'][-1]}), "
            f"{modelo['dados']['n_safras']} safras. Detalhes em `docs/ml.md`."
        )
        tabela = modelo["tabela_metricas"]
        if not tabela.empty:
            st.dataframe(
                tabela[["experimento", "descricao", "skill", "mae_kg_ha", "mape"]].round(3),
                hide_index=True,
            )
        if modelo["figura_skill"]:
            st.image(modelo["figura_skill"])
