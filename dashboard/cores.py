import streamlit as st

# Paleta categorica em ordem fixa, validada para daltonismo nessa ordem
# (separacao entre vizinhas) e contra o fundo branco do dashboard.
PALETA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]


def atribuir(ufs: tuple[str, ...], atribuidas: dict[str, str]) -> dict[str, str]:
    # A cor acompanha a UF, nao a posicao dela na selecao: uma UF fica com a cor
    # que recebeu ao entrar no filtro, e tirar outra UF nao repinta as demais.
    for uf in list(atribuidas):
        if uf not in ufs:
            del atribuidas[uf]
    livres = [cor for cor in PALETA if cor not in atribuidas.values()]
    for uf in ufs:
        if uf not in atribuidas:
            atribuidas[uf] = livres.pop(0)
    return {uf: atribuidas[uf] for uf in ufs}


def por_uf(ufs: tuple[str, ...]) -> dict[str, str]:
    return atribuir(ufs, st.session_state.setdefault("cores_uf", {}))
