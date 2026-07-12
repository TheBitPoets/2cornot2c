from main import somma


def test_somma_con_numero_negativo():
    assert somma(-2, 5) == 3
