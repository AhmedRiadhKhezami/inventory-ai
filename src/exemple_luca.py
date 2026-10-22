from pathlib import Path

import pandas as pd

from src.decision import (CRISE_REELLE, FOURNISSEURS_EXEMPLE, choisir_fournisseur,
                          cout_annuel, faut_il_commander, point_de_bascule,
                          quantite_a_commander, quantite_economique, rentabilite,
                          scenario_crise)

RACINE = Path(__file__).resolve().parent.parent
CHEMIN = RACINE / "data" / "processed" / "usaid_clean.parquet"

# Exemple inventé : Luca vend des coques de téléphone
DEMANDE_JOUR = 20
ECART_TYPE_JOUR = 6
DELAI_PREVU = 35
MARGE_P90 = 31
STOCK = 900
FRAIS_COMMANDE = 400
PRIX_ACHAT = 2.0
MOQ = 1000
CARTON = 100


def charger_usaid():
    df = pd.read_parquet(CHEMIN)
    return df[df["date_prevue"] >= "2010-01-01"]


def routes_usaid(df):
    """Vrais chiffres de retard des 3 routes utilisées en D3 (2010-2015)."""
    routes = {"Chine bateau": ("Direct Drop", "Ocean", "Asie"),
              "Chine avion": ("Direct Drop", "Air", "Asie"),
              "Turquie camion": ("Direct Drop", "Truck", "Europe")}
    print("Routes USAID (2010-2015) :")
    for nom, (via, mode, region) in routes.items():
        r = df[(df["Fulfill Via"] == via) & (df["Shipment Mode"] == mode)
               & (df["region_origine"] == region)]["retard_jours"]
        p90 = r.quantile(0.9)
        au_dela = r[r > p90] - p90
        moyenne = f"{au_dela.mean():.1f} j" if len(au_dela) else "-"
        print(f"  {nom:15s} | {len(r)} lignes | en retard {(r > 0).mean() * 100:.1f} % "
              f"| P90 {p90:.0f} j | au-delà du P90 {(r > p90).mean() * 100:.1f} % "
              f"| dépassement moyen {moyenne}")


def facteur_crise(df):
    """Envois directs par bateau : retards en temps normal et pendant la crise."""
    bateau = df[(df["Fulfill Via"] == "Direct Drop") & (df["Shipment Mode"] == "Ocean")]
    crise = bateau["date_prevue"].between("2010-07-01", "2011-06-30")
    normal = bateau.loc[~crise, "en_retard"].mean()
    pendant = bateau.loc[crise, "en_retard"].mean()
    print(f"Crise : bateau direct en retard {normal * 100:.1f} % ({(~crise).sum()} lignes) "
          f"-> {pendant * 100:.1f} % ({crise.sum()} lignes) de juillet 2010 à juin 2011 "
          f"| facteur x{pendant / normal:.1f}")


def d1():
    for nom, marge in [("Sans marge (benchmark)", 0), ("Avec marge P90", MARGE_P90)]:
        commander, seuil = faut_il_commander(STOCK, 0, DEMANDE_JOUR, ECART_TYPE_JOUR,
                                             DELAI_PREVU, marge)
        print(f"D1 | {nom:22s} | seuil {seuil} | stock {STOCK} | commander : {bool(commander)}")
    print(f"     Le stock dure {STOCK / DEMANDE_JOUR:.0f} j ; livraison jusqu'à "
          f"{DELAI_PREVU + MARGE_P90} j")


def d2():
    _, seuil = faut_il_commander(STOCK, 0, DEMANDE_JOUR, ECART_TYPE_JOUR, DELAI_PREVU, MARGE_P90)
    eoq = quantite_economique(DEMANDE_JOUR, FRAIS_COMMANDE, PRIX_ACHAT)
    for nom, plafond in [("Sans plafond", None), ("Plafond 120 jours", 120)]:
        q, _, _ = quantite_a_commander(STOCK, seuil, DEMANDE_JOUR, FRAIS_COMMANDE, PRIX_ACHAT,
                                       moq=MOQ, carton=CARTON, couverture_max_jours=plafond)
        print(f"D2 | {nom:17s} | EOQ {eoq:.0f} | à commander {q} | payé {q * PRIX_ACHAT:.0f} €")
    for q in [500, 1000, 2400, 3400, 7300]:
        c = cout_annuel(q, DEMANDE_JOUR, FRAIS_COMMANDE, PRIX_ACHAT)
        print(f"     Q = {q:5d} | {DEMANDE_JOUR * 365 / q:4.1f} commandes/an | {c:6.0f} € par an")


def d3_d4():
    for prix_vente in [10.0, 20.0]:
        normal = rentabilite(choisir_fournisseur(FOURNISSEURS_EXEMPLE, DEMANDE_JOUR,
                                                 ECART_TYPE_JOUR, prix_vente),
                             DEMANDE_JOUR, prix_vente)
        crise = rentabilite(choisir_fournisseur(scenario_crise(FOURNISSEURS_EXEMPLE, CRISE_REELLE),
                                                DEMANDE_JOUR, ECART_TYPE_JOUR, prix_vente),
                            DEMANDE_JOUR, prix_vente)
        facteur, nouveau = point_de_bascule(FOURNISSEURS_EXEMPLE, DEMANDE_JOUR,
                                            ECART_TYPE_JOUR, prix_vente)
        print(f"\n===== Produit vendu {prix_vente:.0f} € =====")
        print("Temps normal :")
        print(normal)
        print(f"Crise (x{CRISE_REELLE}) :")
        print(crise[["total", "benefice", "rentable"]])
        print(f"Point de bascule : x{facteur} -> {nouveau}")


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    df = charger_usaid()
    routes_usaid(df)
    facteur_crise(df)
    print()
    d1()
    print()
    d2()
    d3_d4()