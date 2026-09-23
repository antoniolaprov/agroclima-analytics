"""Exporta as tabelas Gold para o JSON que o site estatico consome.

So as colunas que o site usa, com numeros arredondados: as Gold inteiras dao
1,7 MB, contra cerca de 600 KB aqui. Roda depois do dbt, pelo pipeline ou por
`make exportar-web`.

Uso: python scripts/exportar_web.py
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config

DESTINO_PADRAO = config.RAIZ / "web" / "public" / "data"
MALHA = config.RAIZ / "dashboard" / "assets" / "uf_br.geojson"

FONTES = [
    {"nome": "INMET - dados historicos", "url": "https://portal.inmet.gov.br/dadoshistoricos"},
    {"nome": "IBGE - agregados (SIDRA)", "url": "https://servicodados.ibge.gov.br/api/docs/agregados?versao=3"},
    {"nome": "IBGE - malhas", "url": "https://servicodados.ibge.gov.br/api/docs/malhas?versao=3"},
]

# tabela -> (colunas, casas decimais por coluna)
EXTRATOS = {
    "clima": (
        "gold_clima_uf_mensal",
        ["uf", "ano", "mes", "temp_media", "temp_media_movel_3m", "precipitacao",
         "anomalia_temp", "dias_sem_chuva", "n_estacoes"],
        {"temp_media": 1, "temp_media_movel_3m": 1, "anomalia_temp": 1, "precipitacao": 0},
    ),
    "safra": (
        "gold_safra_uf",
        ["uf", "uf_codigo", "cultura", "ano", "producao", "rendimento", "area_colhida", "var_producao_aa"],
        {"producao": 0, "rendimento": 0, "area_colhida": 0, "var_producao_aa": 2},
    ),
    "clima_safra": (
        "gold_clima_safra",
        ["uf", "cultura", "ano", "rendimento", "precip_ciclo", "temp_media_ciclo", "n_estacoes"],
        {"rendimento": 0, "precip_ciclo": 0, "temp_media_ciclo": 1},
    ),
}


def _arredondar(valor, casas):
    if valor is None:
        return None
    return round(float(valor), casas) if casas else int(round(float(valor)))


def _linhas(con, tabela, colunas, casas):
    dados = con.execute(f"select {', '.join(colunas)} from {tabela}").fetchall()
    linhas = []
    for valores in dados:
        linha = dict(zip(colunas, valores))
        for coluna, n in casas.items():
            linha[coluna] = _arredondar(linha[coluna], n)
        linhas.append(linha)
    return linhas


def exportar(caminho_banco: Path = config.DUCKDB_PATH, destino: Path = DESTINO_PADRAO) -> dict[str, int]:
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(caminho_banco), read_only=True)
    try:
        contagem = {}
        for nome, (tabela, colunas, casas) in EXTRATOS.items():
            linhas = _linhas(con, tabela, colunas, casas)
            (destino / f"{nome}.json").write_text(
                json.dumps(linhas, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
            )
            contagem[nome] = len(linhas)

        # ufs vem da uniao das tres tabelas Gold: meta.ufs alimenta o filtro
        # de estado tanto na pagina de Clima quanto na de Safra, entao precisa
        # oferecer qualquer UF presente em qualquer uma delas, nao so na safra.
        ufs = [u for (u,) in con.execute(
            """
            select distinct uf from (
                select uf from gold_clima_uf_mensal
                union select uf from gold_safra_uf
                union select uf from gold_clima_safra
            ) order by 1
            """
        ).fetchall()]
        culturas = [c for (c,) in con.execute("select distinct cultura from gold_safra_uf order by 1").fetchall()]
        anos_clima = [a for (a,) in con.execute("select distinct ano from gold_clima_uf_mensal order by 1").fetchall()]
        anos_safra = [a for (a,) in con.execute("select distinct ano from gold_safra_uf order by 1").fetchall()]
        anos = sorted(set(anos_clima) | set(anos_safra))
    finally:
        con.close()

    meta = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ufs": ufs,
        "culturas": culturas,
        "anos": anos,
        "anos_clima": anos_clima,
        "anos_safra": anos_safra,
        "linhas_por_arquivo": contagem,
        "fontes": FONTES,
    }
    (destino / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.copyfile(MALHA, destino / "uf_br.geojson")
    return contagem


def main() -> None:
    contagem = exportar()
    for nome, linhas in contagem.items():
        print(f"{nome}: {linhas} linhas")


if __name__ == "__main__":
    main()
