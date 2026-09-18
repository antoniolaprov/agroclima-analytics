import plotly.express as px
import streamlit as st

from dashboard import data


def render(filtros):
    st.header("Clima")

    df = data.clima_mensal(filtros["ufs"], filtros["ano_ini"], filtros["ano_fim"])
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    df["competencia"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)

    st.subheader("Temperatura media e media movel de 3 meses")
    fig = px.line(df, x="competencia", y=["temp_media", "temp_media_movel_3m"], color="uf")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Precipitacao acumulada")
    st.plotly_chart(px.bar(df, x="competencia", y="precipitacao", color="uf"), use_container_width=True)

    st.subheader("Anomalia de temperatura")
    st.plotly_chart(px.line(df, x="competencia", y="anomalia_temp", color="uf"), use_container_width=True)

    st.caption("n_estacoes indica quantas estacoes contribuiram para cada ponto.")
    st.dataframe(df[["uf", "competencia", "n_estacoes", "temp_media", "precipitacao"]])
