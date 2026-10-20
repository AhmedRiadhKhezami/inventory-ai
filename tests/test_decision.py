from src.decision import (point_de_commande, faut_il_commander,
                          quantite_economique, cout_annuel, quantite_a_commander)


# ---------- D1 ----------

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


# ---------- D2 ----------

def test_eoq_est_le_cout_le_plus_bas():
    eoq = quantite_economique(20, 400, 2.0)
    cout_eoq = cout_annuel(eoq, 20, 400, 2.0)
    assert cout_eoq <= cout_annuel(eoq / 2, 20, 400, 2.0)
    assert cout_eoq <= cout_annuel(eoq * 2, 20, 400, 2.0)


def test_moq_et_carton_respectes():
    q, _, _ = quantite_a_commander(900, 1000, 1, 400, 2.0, moq=1000, carton=100)
    assert q >= 1000
    assert q % 100 == 0


def test_plafond_ne_coupe_jamais_le_manque():
    q, _, manque = quantite_a_commander(0, 3000, 20, 400, 2.0,
                                        couverture_max_jours=30)
    assert q >= manque