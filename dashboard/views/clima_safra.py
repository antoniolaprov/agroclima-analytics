import plotly.express as px
import streamlit as st

from dashboard import cores, data, graficos

EIXOS = {
    "precip_ciclo": "Chuva acumulada no ciclo (mm)",
    "temp_media_ciclo": "Temperatura media no ciclo (°C)",
}


def render(filtros):
    st.header("Clima x Safra")

    # Uma cultura por vez: o rendimento da cana e o da soja nao cabem num eixo so.
    cultura = filtros["culturas"][0]
    if len(filtros["culturas"]) > 1:
        cultura = st.selectbox("Cultura", filtros["culturas"])

    df = data.clima_safra((cultura,), filtros["ano_ini"], filtros["ano_fim"])
    df = df[df["uf"].isin(filtros["ufs"])]
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    eixo = st.radio("Variavel climatica", list(EIXOS), format_func=EIXOS.get, horizontal=True)

    fig = px.scatter(
        df, x=eixo, y="rendimento", color="uf",
        trendline="ols", trendline_scope="overall", trendline_color_override=graficos.COR_REFERENCIA,
        color_discrete_map=cores.por_uf(filtros["ufs"]),
        hover_data={"ano": True, "n_estacoes": True},
        labels={eixo: EIXOS[eixo], "rendimento": "Rendimento (kg/ha)", "n_estacoes": "Estacoes"},
    )
    fig.update_traces(marker_size=10, selector={"mode": "markers"})
    fig.update_traces(name="Tendencia geral", selector={"mode": "lines"})
    st.plotly_chart(graficos.estilo(fig, legenda=len(filtros["ufs"]) > 1), use_container_width=True)

    n = len(df)
    if n >= 3:
        r = df[eixo].corr(df["rendimento"])
        st.metric("Correlacao (r)", graficos.numero(r, casas=2))
        st.caption(
            f"{n} safras de {cultura} nas UFs selecionadas. Cada ponto e uma UF em um ano; "
            "com poucos anos por UF, a correlacao descreve a amostra e nao prova causa."
        )
    else:
        st.caption(f"Apenas {n} safra(s) com ciclo completo: pouco para calcular correlacao.")

    with st.expander("Ver tabela"):
        st.dataframe(
            df[["uf", "ano", "rendimento", "precip_ciclo", "temp_media_ciclo", "n_estacoes"]],
            hide_index=True,
        )
