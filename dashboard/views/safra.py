import plotly.express as px
import streamlit as st

from dashboard import data


def render(filtros):
    st.header("Safra")

    df = data.safra(filtros["ufs"], filtros["culturas"])
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    st.subheader("Producao por ano")
    st.plotly_chart(px.line(df, x="ano", y="producao", color="uf", line_dash="cultura"), use_container_width=True)

    st.subheader("Rendimento (kg/ha)")
    st.plotly_chart(px.line(df, x="ano", y="rendimento", color="uf", line_dash="cultura"), use_container_width=True)

    st.subheader("Variacao anual da producao (%)")
    st.plotly_chart(px.bar(df, x="ano", y="var_producao_aa", color="uf"), use_container_width=True)
