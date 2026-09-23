import json

import duckdb
import pytest

from scripts import exportar_web


@pytest.fixture
def banco(tmp_path):
    caminho = tmp_path / "w.duckdb"
    con = duckdb.connect(str(caminho))
    con.execute(
        """
        create table gold_clima_uf_mensal as select * from (values
            ('MT', 2024, 1, 26.4321, 26.1, 263.4567, 0.87654, 0, 34, 1.0, 2.0)
        ) as t(uf, ano, mes, temp_media, temp_media_movel_3m, precipitacao,
               anomalia_temp, dias_sem_chuva, n_estacoes, temp_max, temp_min)
        """
    )
    con.execute(
        """
        create table gold_safra_uf as select * from (values
            ('MT', '51', 'soja', 2025, 50175032.4, 3922.6, 12790000.2, 5.4321, 1.0)
        ) as t(uf, uf_codigo, cultura, ano, producao, rendimento, area_colhida,
               var_producao_aa, var_rendimento_aa)
        """
    )
    con.execute(
        """
        create table gold_clima_safra as select * from (values
            ('MT', 'soja', 2025, 3922.6, 1349.4, 25.55, 34, 6, 6),
            ('RS', 'soja', 2025, 2012.1, 660.2, 21.11, 43, 6, 6)
        ) as t(uf, cultura, ano, rendimento, precip_ciclo, temp_media_ciclo,
               n_estacoes, meses_observados, meses_esperados)
        """
    )
    con.close()
    return caminho


def test_exporta_um_arquivo_por_tabela(banco, tmp_path):
    destino = tmp_path / "data"
    resultado = exportar_web.exportar(banco, destino)

    assert set(resultado) == {"clima", "safra", "clima_safra"}
    for nome in ("clima.json", "safra.json", "clima_safra.json", "meta.json", "uf_br.geojson"):
        assert (destino / nome).exists(), nome


def test_exporta_so_as_colunas_do_site(banco, tmp_path):
    destino = tmp_path / "data"
    exportar_web.exportar(banco, destino)

    clima = json.loads((destino / "clima.json").read_text(encoding="utf-8"))
    assert set(clima[0]) == {
        "uf", "ano", "mes", "temp_media", "temp_media_movel_3m",
        "precipitacao", "anomalia_temp", "dias_sem_chuva", "n_estacoes",
    }
    safra = json.loads((destino / "safra.json").read_text(encoding="utf-8"))
    assert set(safra[0]) == {
        "uf", "uf_codigo", "cultura", "ano", "producao", "rendimento", "area_colhida", "var_producao_aa",
    }
    assert safra[0]["uf_codigo"] == "51"


def test_arredonda_os_numeros(banco, tmp_path):
    destino = tmp_path / "data"
    exportar_web.exportar(banco, destino)

    clima = json.loads((destino / "clima.json").read_text(encoding="utf-8"))[0]
    assert clima["temp_media"] == 26.4
    assert clima["precipitacao"] == 263
    assert clima["anomalia_temp"] == 0.9

    safra = json.loads((destino / "safra.json").read_text(encoding="utf-8"))[0]
    assert safra["producao"] == 50175032
    assert safra["var_producao_aa"] == 5.43


def test_preserva_ausencia_como_null(banco, tmp_path):
    con = duckdb.connect(str(banco))
    con.execute("update gold_safra_uf set var_producao_aa = null")
    con.close()

    destino = tmp_path / "data"
    exportar_web.exportar(banco, destino)

    safra = json.loads((destino / "safra.json").read_text(encoding="utf-8"))[0]
    assert safra["var_producao_aa"] is None


def test_meta_descreve_o_extrato(banco, tmp_path):
    destino = tmp_path / "data"
    exportar_web.exportar(banco, destino)

    meta = json.loads((destino / "meta.json").read_text(encoding="utf-8"))
    assert meta["ufs"] == ["MT", "RS"]
    assert meta["culturas"] == ["soja"]
    assert meta["anos"] == [2024, 2025]
    assert meta["anos_clima"] == [2024]
    assert meta["anos_safra"] == [2025]
    assert meta["linhas_por_arquivo"]["clima"] == 1
    assert meta["gerado_em"].startswith("20")
    assert meta["fontes"]
