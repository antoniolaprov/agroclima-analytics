import time

import duckdb
import pandas as pd
import streamlit as st

from src import config


def consultar(sql: str, params: list | None = None) -> pd.DataFrame:
    for tentativa in range(3):
        try:
            con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
            try:
                return con.execute(sql, params or []).fetch_df()
            finally:
                con.close()
        except duckdb.IOException:
            if tentativa == 2:
                raise
            time.sleep(1)


@st.cache_data(ttl=600)
def clima_mensal(ufs: tuple[str, ...], ano_ini: int, ano_fim: int) -> pd.DataFrame:
    marcadores = ", ".join("?" for _ in ufs)
    return consultar(
        f"""
        select * from gold_clima_uf_mensal
        where uf in ({marcadores}) and ano between ? and ?
        order by ano, mes
        """,
        list(ufs) + [ano_ini, ano_fim],
    )


@st.cache_data(ttl=600)
def safra(ufs: tuple[str, ...], culturas: tuple[str, ...], ano_ini: int, ano_fim: int) -> pd.DataFrame:
    m_uf = ", ".join("?" for _ in ufs)
    m_cult = ", ".join("?" for _ in culturas)
    return consultar(
        f"""
        select * from gold_safra_uf
        where uf in ({m_uf}) and cultura in ({m_cult}) and ano between ? and ?
        order by ano
        """,
        list(ufs) + list(culturas) + [ano_ini, ano_fim],
    )


@st.cache_data(ttl=600)
def clima_safra(culturas: tuple[str, ...], ano_ini: int, ano_fim: int) -> pd.DataFrame:
    marcadores = ", ".join("?" for _ in culturas)
    return consultar(
        f"select * from gold_clima_safra where cultura in ({marcadores}) and ano between ? and ?",
        list(culturas) + [ano_ini, ano_fim],
    )


@st.cache_data(ttl=600)
def producao_por_uf(cultura: str, ano_ini: int, ano_fim: int) -> pd.DataFrame:
    return consultar(
        """
        select uf_codigo, uf, ano, producao
        from gold_safra_uf
        where cultura = ?
          and ano = (
              select max(ano) from gold_safra_uf
              where cultura = ? and ano between ? and ?
          )
        order by uf
        """,
        [cultura, cultura, ano_ini, ano_fim],
    )
