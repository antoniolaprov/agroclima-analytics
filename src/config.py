from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA_DIR = RAIZ / "data"
BRONZE_DIR = DATA_DIR / "bronze"
DUCKDB_PATH = DATA_DIR / "warehouse.duckdb"

# 2001 em diante: o zip de 2000 cobre so as poucas estacoes instaladas no fim
# daquele ano. A primeira carga baixa cerca de 1,5 GB.
ANOS_CLIMA = tuple(range(2001, 2027))

INMET_ESTACOES_URL = "https://apitempo.inmet.gov.br/estacoes/T"
INMET_ZIP_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"

SIDRA_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

CULTURAS_PAM = {
    "40124": "soja",
    "40122": "milho",
    "40139": "cafe",
    "40106": "cana",
}

CULTURAS_LSPA = {
    "39443": "soja",
    "39441": "milho",
    "39442": "milho",
    "40527": "cafe",
    "39456": "cana",
}

CICLO_LSPA = {"39441": 1, "39442": 2}
