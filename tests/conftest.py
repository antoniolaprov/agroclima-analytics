import numpy as np
import pandas as pd
import pytest

UFS_SINTETICAS = ["GO", "MG", "MT", "PR", "RS", "SP"]
CICLO_SINTETICO = pd.DataFrame(
    {"cultura": ["soja", "milho"], "mes_inicio": [10, 9], "mes_fim": [3, 7]}
)


def gerar_dados(semente: int = 7, efeito_chuva: float = 0.5, ruido: float = 0.03) -> dict:
    """Safra 1990-2026 e clima mensal 2001-2026 em que a anomalia de
    rendimento depende da chuva da fase 2 do ciclo (relativa ao normal).
    Sem clima antes de 2001, como no warehouse real."""
    rng = np.random.default_rng(semente)
    clima = []
    for uf in UFS_SINTETICAS:
        normal = rng.uniform(40, 250, size=12)
        for ano in range(2001, 2027):
            for mes in range(1, 13):
                clima.append(
                    {
                        "uf": uf, "ano": ano, "mes": mes,
                        "temp_media": 22 + 4 * np.cos((mes - 1) / 12 * 2 * np.pi) + rng.normal(0, 0.5),
                        "temp_max": 29 + rng.normal(0, 1),
                        "precipitacao": normal[mes - 1] * rng.lognormal(0, 0.35),
                        "dias_sem_chuva": int(rng.integers(5, 25)),
                        "n_estacoes": 3,
                    }
                )
    clima = pd.DataFrame(clima)

    # Chuva relativa da fase 2 de cada safra, calculada direto: soja dez-jan,
    # milho jan-abr (os tercos do meio dos ciclos out-mar e set-jul).
    meses_f2 = {"soja": [(12, -1), (1, 0)], "milho": [(1, 0), (2, 0), (3, 0)]}
    media = clima.groupby(["uf", "mes"])["precipitacao"].mean()
    indexado = clima.set_index(["uf", "ano", "mes"])["precipitacao"]

    safra = []
    for uf in UFS_SINTETICAS:
        for cultura in ("soja", "milho"):
            base = rng.uniform(7.6, 8.4)
            for ano in range(1990, 2027):
                sinal = 0.0
                if ano >= 2002:
                    obs = sum(indexado[(uf, ano + d, m)] for m, d in meses_f2[cultura])
                    norm = sum(media[(uf, m)] for m, _ in meses_f2[cultura])
                    sinal = efeito_chuva * np.clip(obs / norm - 1, -0.6, 0.6)
                log_rend = base + 0.02 * (ano - 1990) + sinal + rng.normal(0, ruido)
                safra.append(
                    {"uf": uf, "cultura": cultura, "ano": ano,
                     "rendimento": float(np.exp(log_rend)), "area_colhida": 1000.0}
                )
    return {"safra": pd.DataFrame(safra), "clima": clima, "ciclo": CICLO_SINTETICO.copy()}


@pytest.fixture(scope="session")
def dados_sinteticos():
    return gerar_dados()
