import numpy as np
import pandas as pd
import pytest

from src.ml import features

CICLO = pd.DataFrame({"cultura": ["soja", "cana"], "mes_inicio": [10, 4], "mes_fim": [3, 11]})


def _clima(ufs=("MT",), anos=range(2001, 2012), chuva=100.0):
    linhas = [
        {"uf": uf, "ano": a, "mes": m, "temp_media": 25.0, "temp_max": 31.0,
         "precipitacao": chuva, "dias_sem_chuva": 10, "n_estacoes": 2}
        for uf in ufs for a in anos for m in range(1, 13)
    ]
    return pd.DataFrame(linhas)


def test_ciclo_que_atravessa_o_ano_desloca_os_primeiros_meses():
    meses = features.meses_do_ciclo(CICLO).query("cultura == 'soja'").set_index("mes")
    assert meses.loc[[10, 11, 12], "desloca_ano"].eq(1).all()
    assert meses.loc[[1, 2, 3], "desloca_ano"].eq(0).all()


def test_fases_dividem_o_ciclo_em_tercos():
    meses = features.meses_do_ciclo(CICLO).query("cultura == 'soja'").set_index("mes")
    assert meses["fase"].to_dict() == {10: 1, 11: 1, 12: 2, 1: 2, 2: 3, 3: 3}


def test_ciclo_de_oito_meses_tem_fases_desiguais_mas_completas():
    meses = features.meses_do_ciclo(CICLO).query("cultura == 'cana'")
    assert len(meses) == 8
    assert sorted(meses["fase"].unique()) == [1, 2, 3]


def test_meses_de_outubro_entram_na_safra_do_ano_seguinte():
    clima = _clima(anos=[2010, 2011])
    clima.loc[(clima["ano"] == 2010) & (clima["mes"] == 10), "precipitacao"] = 400.0
    saida = features.clima_da_safra(clima, CICLO.iloc[:1]).set_index("ano")
    assert saida.loc[2011, "chuva_f1"] == 500.0


def test_safra_com_mes_sem_chuva_medida_e_descartada():
    clima = _clima(anos=[2010, 2011])
    clima.loc[(clima["ano"] == 2011) & (clima["mes"] == 1), "precipitacao"] = np.nan
    saida = features.clima_da_safra(clima, CICLO.iloc[:1])
    assert 2011 not in set(saida["ano"])


def test_horizonte_so_exige_os_meses_observados():
    clima = _clima(anos=[2010, 2011])
    clima.loc[(clima["ano"] == 2011) & (clima["mes"] == 3), "precipitacao"] = np.nan
    h1 = features.clima_da_safra(clima, CICLO.iloc[:1], horizonte=1)
    h3 = features.clima_da_safra(clima, CICLO.iloc[:1], horizonte=3)
    assert 2011 in set(h1["ano"]) and 2011 not in set(h3["ano"])
    assert "chuva_f2" not in h1.columns


def test_horizonte_invalido():
    with pytest.raises(ValueError):
        features.clima_da_safra(_clima(), CICLO, horizonte=4)


def test_normal_usa_so_anos_anteriores():
    clima = _clima(anos=range(2001, 2010))
    clima.loc[clima["ano"] == 2009, "precipitacao"] = 1000.0
    normais = features.com_normais(clima).set_index(["ano", "mes"])
    assert normais.loc[(2009, 1), "precip_normal"] == 100.0
    assert np.isnan(normais.loc[(2004, 1), "precip_normal"])


def test_chuva_relativa_mede_desvio_da_normal():
    clima = _clima(anos=range(2001, 2012))
    clima.loc[(clima["ano"] == 2010) & (clima["mes"] == 12), "precipitacao"] = 50.0
    clima.loc[(clima["ano"] == 2011) & (clima["mes"] == 1), "precipitacao"] = 50.0
    saida = features.clima_da_safra(clima, CICLO.iloc[:1]).set_index("ano")
    assert saida.loc[2011, "chuva_rel_f2"] == pytest.approx(-0.5)
    assert saida.loc[2011, "pior_mes_rel"] == pytest.approx(-0.5)


def test_colunas_clima_batem_com_as_geradas():
    saida = features.clima_da_safra(_clima(), CICLO, horizonte=2)
    assert set(features.colunas_clima(2)) <= set(saida.columns)


def test_tabela_tem_alvo_e_categoricas(dados_sinteticos):
    tabela = features.montar_tabela(dados_sinteticos["safra"], dados_sinteticos["clima"],
                                    dados_sinteticos["ciclo"])
    assert tabela["anomalia"].notna().all()
    assert tabela["cultura"].dtype == "category"
    assert not {"area_colhida"} & set(features.colunas_clima(3))
