import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard import cores, data, graficos

SERIES_TEMPERATURA = {
    "temp_media": "Media do mes",
    "temp_media_movel_3m": "Media movel de 3 meses",
}


def render(filtros):
    st.header("Clima")

    df = data.clima_mensal(filtros["ufs"], filtros["ano_ini"], filtros["ano_fim"])
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    df["mes_ref"] = pd.to_datetime({"year": df["ano"], "month": df["mes"], "day": 1})
    cor = cores.por_uf(filtros["ufs"])
    varias_ufs = len(filtros["ufs"]) > 1

    st.subheader("Temperatura media (°C)")
    temperatura = df.melt(
        id_vars=["uf", "mes_ref"],
        value_vars=list(SERIES_TEMPERATURA),
        var_name="serie",
        value_name="temperatura",
    )
    temperatura["serie"] = temperatura["serie"].map(SERIES_TEMPERATURA)
    fig = px.line(
        temperatura, x="mes_ref", y="temperatura", color="uf", line_dash="serie",
        color_discrete_map=cor, labels={"mes_ref": "", "temperatura": "°C", "serie": ""},
    )
    st.plotly_chart(graficos.estilo(fig), use_container_width=True)

    st.subheader("Precipitacao mensal (mm)")
    st.caption("Media entre as estacoes de cada UF.")
    fig = px.line(
        df, x="mes_ref", y="precipitacao", color="uf",
        color_discrete_map=cor, labels={"mes_ref": "", "precipitacao": "mm"},
    )
    st.plotly_chart(graficos.estilo(fig, legenda=varias_ufs), use_container_width=True)

    st.subheader("Anomalia de temperatura (°C)")
    st.caption("Diferenca para a media do mesmo mes em 2022-2026, nao para uma normal de 30 anos.")
    fig = px.line(
        df, x="mes_ref", y="anomalia_temp", color="uf",
        color_discrete_map=cor, labels={"mes_ref": "", "anomalia_temp": "°C"},
    )
    fig = graficos.linha_de_zero(graficos.estilo(fig, legenda=varias_ufs))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver tabela"):
        st.caption("n_estacoes indica quantas estacoes contribuiram para cada mes.")
        st.dataframe(
            df[["uf", "ano", "mes", "n_estacoes", "temp_media", "precipitacao", "dias_sem_chuva", "anomalia_temp"]],
            hide_index=True,
        )
