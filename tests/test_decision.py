from src.decision import point_de_commande, faut_il_commander


def test_marge_retard_augmente_le_seuil():
    sans = point_de_commande(20, 6, 35, 0)
    avec = point_de_commande(20, 6, 35, 31)
    assert avec > sans


def test_stock_en_route_est_compte():
    sans_en_route, _ = faut_il_commander(900, 0, 20, 6, 35, 31)
    avec_en_route, _ = faut_il_commander(900, 600, 20, 6, 35, 31)
    assert sans_en_route
    assert not avec_en_route


def test_pas_de_demande_pas_de_seuil():
    assert point_de_commande(0, 0, 35, 31) == 0