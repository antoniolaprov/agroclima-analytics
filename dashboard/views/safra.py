import plotly.express as px
import streamlit as st

from dashboard import cores, data, graficos

ROTULOS = {
    "ano": "",
    "producao": "Producao (t)",
    "rendimento": "Rendimento (kg/ha)",
    "var_producao_aa": "Variacao (%)",
    "cultura": "",
}


def _por_cultura(fig, n_culturas):
    # Cada cultura em seu painel e com seu proprio eixo: o rendimento da cana
    # (dezenas de milhares de kg/ha) achataria o da soja num eixo comum.
    fig.update_xaxes(dtick=1, tickformat="d")
    if n_culturas > 1:
        fig.update_yaxes(matches=None)
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(height=260 * n_culturas)
    return fig


def render(filtros):
    st.header("Safra")

    df = data.safra(filtros["ufs"], filtros["culturas"], filtros["ano_ini"], filtros["ano_fim"])
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    cor = cores.por_uf(filtros["ufs"])
    n_culturas = df["cultura"].nunique()
    painel = {"facet_row": "cultura"} if n_culturas > 1 else {}
    legenda = len(filtros["ufs"]) > 1

    for coluna, titulo in (("producao", "Producao por ano (t)"), ("rendimento", "Rendimento (kg/ha)")):
        st.subheader(titulo)
        fig = px.line(
            df, x="ano", y=coluna, color="uf", markers=True,
            color_discrete_map=cor, labels=ROTULOS, **painel,
        )
        st.plotly_chart(graficos.estilo(_por_cultura(fig, n_culturas), legenda), use_container_width=True)

    st.subheader("Variacao anual da producao (%)")
    st.caption("Sem barra quando a PAM nao tem o ano anterior para aquela UF.")
    fig = px.bar(
        df.dropna(subset=["var_producao_aa"]), x="ano", y="var_producao_aa", color="uf",
        barmode="group", color_discrete_map=cor, labels=ROTULOS, **painel,
    )
    fig = graficos.linha_de_zero(_por_cultura(fig, n_culturas))
    st.plotly_chart(graficos.estilo(fig, legenda), use_container_width=True)

    with st.expander("Ver tabela"):
        st.dataframe(
            df[["uf", "cultura", "ano", "producao", "rendimento", "area_colhida", "var_producao_aa"]],
            hide_index=True,
        )
