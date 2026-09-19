import plotly.express as px
import streamlit as st

from dashboard import data


def render(filtros):
    st.header("Visao geral")

    df = data.safra(filtros["ufs"], filtros["culturas"], filtros["ano_ini"], filtros["ano_fim"])
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    ultimo = df[df["ano"] == df["ano"].max()]
    col1, col2, col3 = st.columns(3)
    col1.metric("Producao total (t)", f"{ultimo['producao'].sum():,.0f}")
    col2.metric("Rendimento medio (kg/ha)", f"{ultimo['rendimento'].mean():,.0f}")
    col3.metric("Area colhida (ha)", f"{ultimo['area_colhida'].sum():,.0f}")

    st.subheader(f"Producao por UF em {int(df['ano'].max())}")
    fig = px.bar(ultimo.sort_values("producao"), x="producao", y="uf", color="cultura", orientation="h")
    st.plotly_chart(fig, use_container_width=True)
