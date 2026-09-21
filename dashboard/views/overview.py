import json
from functools import cache
from pathlib import Path

import plotly.express as px
import streamlit as st

from dashboard import data

MALHA_UFS = Path(__file__).resolve().parent.parent / "assets" / "uf_br.geojson"


@cache
def malha_ufs() -> dict:
    # Malha das UFs da API de malhas do IBGE (qualidade intermediaria), versionada
    # para o dashboard nao depender da API no ar. `codarea` e o codigo IBGE da UF.
    # O IBGE segue a RFC 7946 (anel externo anti-horario), mas o d3-geo que o
    # plotly usa espera o sentido oposto e, sem inverter, pinta o mapa inteiro.
    malha = json.loads(MALHA_UFS.read_text(encoding="utf-8"))
    for feature in malha["features"]:
        geometria = feature["geometry"]
        poligonos = geometria["coordinates"]
        if geometria["type"] == "Polygon":
            poligonos = [poligonos]
        for poligono in poligonos:
            for anel in poligono:
                anel.reverse()
    return malha


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

    cultura = filtros["culturas"][0]
    if len(filtros["culturas"]) > 1:
        cultura = st.selectbox("Cultura no mapa", filtros["culturas"])

    mapa = data.producao_por_uf(cultura, filtros["ano_ini"], filtros["ano_fim"])
    if not mapa.empty:
        ano_mapa = int(mapa["ano"].iloc[0])
        st.subheader(f"Producao de {cultura} por UF em {ano_mapa} (todas as UFs)")
        fig = px.choropleth(
            mapa,
            geojson=malha_ufs(),
            locations="uf_codigo",
            featureidkey="properties.codarea",
            color="producao",
            color_continuous_scale="Greens",
            hover_name="uf",
            hover_data={"uf_codigo": False, "producao": ":,.0f"},
            labels={"producao": "Producao (t)"},
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, height=520)
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})
        with st.expander("Ver tabela do mapa"):
            st.dataframe(
                mapa.sort_values("producao", ascending=False)[["uf", "producao"]],
                hide_index=True,
            )

    st.subheader(f"Producao por UF selecionada em {int(df['ano'].max())}")
    fig = px.bar(ultimo.sort_values("producao"), x="producao", y="uf", color="cultura", orientation="h")
    st.plotly_chart(fig, use_container_width=True)
