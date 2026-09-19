import streamlit as st

from dashboard.views import clima, clima_safra, overview, safra

st.set_page_config(page_title="AgroClima Analytics", layout="wide")

PAGINAS = {
    "Visao geral": overview,
    "Clima": clima,
    "Safra": safra,
    "Clima x Safra": clima_safra,
}

UFS = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA",
    "PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO",
]
CULTURAS = ["soja", "milho", "cafe", "cana"]

st.sidebar.title("AgroClima")
pagina = st.sidebar.radio("Pagina", list(PAGINAS))

filtros = {
    "ufs": tuple(st.sidebar.multiselect("UF", UFS, default=["MT", "PR", "RS"])),
    "culturas": tuple(st.sidebar.multiselect("Cultura", CULTURAS, default=["soja"])),
    "ano_ini": st.sidebar.number_input("Ano inicial", 2022, 2026, 2022),
    "ano_fim": st.sidebar.number_input("Ano final", 2022, 2026, 2026),
}

if not filtros["ufs"] or not filtros["culturas"]:
    st.warning("Selecione ao menos uma UF e uma cultura.")
else:
    PAGINAS[pagina].render(filtros)
