from src.decision import (point_de_commande, faut_il_commander,
                          quantite_economique, cout_annuel, quantite_a_commander,
                          cout_total_fournisseur, choisir_fournisseur,
                          FOURNISSEURS_EXEMPLE, rentabilite, scenario_crise,
                          point_de_bascule)


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


# ---------- D3 ----------

def test_plus_de_retard_coute_plus_cher():
    f = dict(FOURNISSEURS_EXEMPLE["Chine bateau"])
    normal = cout_total_fournisseur(f, 20, 6, 10.0)["total"]
    f["p_depasse"] = 0.30
    crise = cout_total_fournisseur(f, 20, 6, 10.0)["total"]
    assert crise > normal


def test_sans_retard_pas_de_ventes_perdues():
    couts = cout_total_fournisseur(FOURNISSEURS_EXEMPLE["Turquie camion"], 20, 6, 10.0)
    assert couts["ventes_perdues"] == 0


def test_premier_du_tableau_est_le_moins_cher():
    tableau = choisir_fournisseur(FOURNISSEURS_EXEMPLE, 20, 6, 10.0)
    assert tableau["total"].iloc[0] == tableau["total"].min()


# ---------- D4 ----------

def test_prix_trop_bas_pas_rentable():
    tableau = choisir_fournisseur(FOURNISSEURS_EXEMPLE, 20, 6, 2.2)
    tableau = rentabilite(tableau, 20, 2.2)
    assert not tableau["rentable"].any()


def test_crise_ne_modifie_pas_les_vrais_chiffres():
    scenario_crise(FOURNISSEURS_EXEMPLE, 3.2)
    assert FOURNISSEURS_EXEMPLE["Chine bateau"]["p_depasse"] == 0.10


def test_produit_cher_bascule_plus_vite():
    facteur_10, _ = point_de_bascule(FOURNISSEURS_EXEMPLE, 20, 6, 10.0)
    facteur_20, choix_20 = point_de_bascule(FOURNISSEURS_EXEMPLE, 20, 6, 20.0)
    assert facteur_20 < facteur_10
    assert choix_20 == "Turquie camion"