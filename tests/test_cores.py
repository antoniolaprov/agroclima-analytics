from dashboard import cores


def test_cada_uf_recebe_uma_cor_distinta():
    atribuidas = {}
    mapa = cores.atribuir(("MT", "PR", "RS"), atribuidas)
    assert len(set(mapa.values())) == 3
    assert set(mapa.values()) <= set(cores.PALETA)


def test_tirar_uma_uf_nao_repinta_as_outras():
    atribuidas = {}
    antes = cores.atribuir(("MT", "PR", "RS"), atribuidas)
    depois = cores.atribuir(("PR", "RS"), atribuidas)
    assert depois == {"PR": antes["PR"], "RS": antes["RS"]}


def test_uf_nova_ocupa_a_cor_que_ficou_livre():
    atribuidas = {}
    antes = cores.atribuir(("MT", "PR", "RS"), atribuidas)
    depois = cores.atribuir(("PR", "RS", "GO"), atribuidas)
    assert depois["GO"] == antes["MT"]
    assert depois["PR"] == antes["PR"]


def test_oito_ufs_esgotam_a_paleta_sem_repetir_cor():
    atribuidas = {}
    ufs = ("AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES")
    mapa = cores.atribuir(ufs, atribuidas)
    assert len(set(mapa.values())) == len(cores.PALETA) == 8
