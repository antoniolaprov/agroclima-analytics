from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA_DIR = RAIZ / "data"
BRONZE_DIR = DATA_DIR / "bronze"
DUCKDB_PATH = DATA_DIR / "warehouse.duckdb"

ANOS_CLIMA = (2022, 2023, 2024, 2025, 2026)

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
