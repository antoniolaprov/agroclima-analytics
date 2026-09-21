from dashboard import graficos


def test_numero_usa_formato_brasileiro():
    assert graficos.numero(85127196) == "85.127.196"
    assert graficos.numero(3194.4) == "3.194"
    assert graficos.numero(0.4567, casas=2) == "0,46"
    assert graficos.numero(-1234.5, casas=1) == "-1.234,5"


def test_numero_sem_valor_vira_traco():
    assert graficos.numero(float("nan")) == "-"
    assert graficos.numero(float("inf")) == "-"
