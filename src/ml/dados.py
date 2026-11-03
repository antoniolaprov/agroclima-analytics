import time
from pathlib import Path

import duckdb
import pandas as pd

from src import config

SQL_SAFRA = """
    select uf, cultura, ano, rendimento, area_colhida
    from gold_safra_uf
    where rendimento is not null and rendimento > 0
"""

SQL_CLIMA = """
    select uf, ano, mes, temp_media, temp_max, precipitacao, dias_sem_chuva, n_estacoes
    from gold_clima_uf_mensal
"""

SQL_CICLO = "select cultura, mes_inicio, mes_fim from ciclo_cultura"


def _conectar(caminho: Path) -> duckdb.DuckDBPyConnection:
    # Mesmo cuidado do dashboard: o dbt pode estar com o arquivo aberto para
    # escrita no momento em que o treino comeca.
    for tentativa in range(3):
        try:
            return duckdb.connect(str(caminho), read_only=True)
        except duckdb.IOException:
            if tentativa == 2:
                raise
            time.sleep(1)


def carregar(caminho: Path | None = None) -> dict[str, pd.DataFrame]:
    con = _conectar(caminho or config.DUCKDB_PATH)
    try:
        return {
            "safra": con.execute(SQL_SAFRA).fetch_df(),
            "clima": con.execute(SQL_CLIMA).fetch_df(),
            "ciclo": con.execute(SQL_CICLO).fetch_df(),
        }
    finally:
        con.close()
