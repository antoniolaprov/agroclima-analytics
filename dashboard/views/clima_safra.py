import plotly.express as px
import streamlit as st

from dashboard import data


def render(filtros):
    st.header("Clima x Safra")

    df = data.clima_safra(filtros["culturas"])
    df = df[df["uf"].isin(filtros["ufs"])]
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    eixo = st.radio("Variavel climatica", ["precip_ciclo", "temp_media_ciclo"], horizontal=True)

    fig = px.scatter(
        df, x=eixo, y="rendimento", color="uf", symbol="cultura",
        trendline="ols", hover_data=["ano", "n_estacoes"],
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Correlacao por cultura")
    correl = (
        df.groupby("cultura")[[eixo, "rendimento"]]
        .corr().unstack().iloc[:, 1].rename("correlacao").reset_index()
    )
    st.dataframe(correl)
