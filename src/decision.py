import copy

import numpy as np
import pandas as pd

# z = 1.65 -> on veut couvrir 95% des variations de la demande
Z_SERVICE = 1.65


# ---------- D1 : QUAND commander ----------

def stock_securite(ecart_type_jour, jours_couverts, z=Z_SERVICE):
    """Stock en plus pour les jours où on vend plus que prévu."""
    return z * ecart_type_jour * np.sqrt(jours_couverts)


def point_de_commande(demande_jour, ecart_type_jour, delai_prevu, marge_retard):
    """Niveau de stock en dessous duquel il faut commander."""
    jours_couverts = delai_prevu + marge_retard
    besoin = demande_jour * jours_couverts
    securite = stock_securite(ecart_type_jour, jours_couverts)
    return besoin + securite


def faut_il_commander(stock_actuel, en_route, demande_jour, ecart_type_jour,
                      delai_prevu, marge_retard):
    """Renvoie (True/False, seuil)."""
    seuil = point_de_commande(demande_jour, ecart_type_jour,
                              delai_prevu, marge_retard)
    stock_total = stock_actuel + en_route
    return stock_total <= seuil, round(seuil)


# ---------- D2 : COMBIEN commander ----------

def quantite_economique(demande_jour, frais_par_commande, prix_achat,
                        taux_stockage=0.25):
    """EOQ : quantité qui rend le coût total (commandes + stockage) le plus bas."""
    demande_an = demande_jour * 365
    cout_stockage_unite = prix_achat * taux_stockage   # coût par pièce par an
    return np.sqrt(2 * demande_an * frais_par_commande / cout_stockage_unite)


def cout_annuel(quantite, demande_jour, frais_par_commande, prix_achat,
                taux_stockage=0.25):
    """Coût par an : frais de commande + coût de stockage."""
    demande_an = demande_jour * 365
    nb_commandes = demande_an / quantite
    stock_moyen = quantite / 2
    return nb_commandes * frais_par_commande + stock_moyen * prix_achat * taux_stockage


def quantite_a_commander(stock_total, seuil, demande_jour, frais_par_commande,
                         prix_achat, moq=0, carton=1, couverture_max_jours=None):
    """Quantité finale avec les règles réelles : manque, EOQ, plafond, MOQ, carton."""
    manque = max(seuil - stock_total, 0)
    eoq = quantite_economique(demande_jour, frais_par_commande, prix_achat)

    quantite = max(eoq, manque)
    if couverture_max_jours is not None:
        quantite = min(quantite, demande_jour * couverture_max_jours)
    quantite = max(quantite, manque, moq)

    quantite = int(np.ceil(quantite / carton) * carton)
    return quantite, round(eoq), round(manque)


# ---------- D3 : CHEZ QUI commander ----------

def cout_total_fournisseur(f, demande_jour, ecart_type_jour, prix_vente,
                           taux_stockage=0.25):
    """Coût total sur un an pour un fournisseur, en 4 parties."""
    demande_an = demande_jour * 365
    cout_unite = f["prix"] + f["transport_unite"]

    # 1. Achat + transport de toutes les pièces de l'année
    achat = demande_an * cout_unite

    # 2. Frais de commande + stockage normal (avec la quantité EOQ)
    eoq = quantite_economique(demande_jour, f["frais_commande"], cout_unite,
                              taux_stockage)
    commandes_stockage = cout_annuel(eoq, demande_jour, f["frais_commande"],
                                     cout_unite, taux_stockage)

    # 3. Stock tampon pour se protéger du retard (marge P90 + sécurité)
    pieces_tampon = (demande_jour * f["marge_p90"]
                     + stock_securite(ecart_type_jour, f["delai"] + f["marge_p90"]))
    tampon = pieces_tampon * cout_unite * taux_stockage

    # 4. Ventes perdues quand le retard dépasse même la marge
    nb_commandes = demande_an / eoq
    pieces_perdues = nb_commandes * f["p_depasse"] * demande_jour * f["depassement_jours"]
    ventes_perdues = pieces_perdues * (prix_vente - cout_unite)

    total = achat + commandes_stockage + tampon + ventes_perdues
    return {"achat": achat, "commandes_stockage": commandes_stockage,
            "tampon_retard": tampon, "ventes_perdues": ventes_perdues,
            "total": total}


def choisir_fournisseur(fournisseurs, demande_jour, ecart_type_jour, prix_vente):
    """Tableau des coûts, du moins cher au plus cher."""
    lignes = {nom: cout_total_fournisseur(f, demande_jour, ecart_type_jour, prix_vente)
              for nom, f in fournisseurs.items()}
    tableau = pd.DataFrame(lignes).T.round(0).astype(int)
    return tableau.sort_values("total")


# Les chiffres de retard viennent de USAID (module 2), par route :
#   usine -> bateau -> Asie  : 18.6% en retard, marge P90 = 31 j, dépassement moyen 32.6 j
#   usine -> avion  -> Asie  :  8.8% en retard, marge P90 = 0 j,  retard moyen 19.1 j
#   usine -> camion -> Europe:  0.0% en retard (139 envois)
# Les prix, frais et noms de pays sont inventés pour l'exemple.
FOURNISSEURS_EXEMPLE = {
    "Chine bateau": {"prix": 2.00, "transport_unite": 0.10, "frais_commande": 400,
                     "delai": 35, "marge_p90": 31, "p_depasse": 0.10,
                     "depassement_jours": 32.6},
    "Chine avion": {"prix": 2.00, "transport_unite": 0.80, "frais_commande": 300,
                    "delai": 10, "marge_p90": 0, "p_depasse": 0.088,
                    "depassement_jours": 19.1},
    "Turquie camion": {"prix": 2.60, "transport_unite": 0.20, "frais_commande": 250,
                       "delai": 10, "marge_p90": 0, "p_depasse": 0.0,
                       "depassement_jours": 0},
}


# ---------- D4 : EST-CE RENTABLE, ET SI UNE CRISE ARRIVE ? ----------

# Crise réelle mesurée sur USAID (juillet 2010 - juin 2011, pic du GSCPI) :
#   usine -> bateau : 9.9% en retard en temps normal, 31.6% pendant la crise -> x3.2
CRISE_REELLE = 3.2


def rentabilite(tableau, demande_jour, prix_vente):
    """Ajoute le bénéfice par an et dit si c'est rentable."""
    t = tableau.copy()
    chiffre_affaires = demande_jour * 365 * prix_vente
    t["benefice"] = (chiffre_affaires - t["total"]).astype(int)
    t["rentable"] = t["benefice"] > 0
    return t


def scenario_crise(fournisseurs, facteur):
    """Copie des fournisseurs où les gros retards arrivent 'facteur' fois plus souvent."""
    crise = copy.deepcopy(fournisseurs)
    for f in crise.values():
        f["p_depasse"] = min(f["p_depasse"] * facteur, 1.0)
    return crise


def point_de_bascule(fournisseurs, demande_jour, ecart_type_jour, prix_vente,
                     facteur_max=10, pas=0.1):
    """Plus petit facteur de crise qui change le fournisseur recommandé."""
    choix_normal = choisir_fournisseur(fournisseurs, demande_jour,
                                       ecart_type_jour, prix_vente).index[0]
    for facteur in np.arange(1, facteur_max + pas, pas):
        crise = scenario_crise(fournisseurs, facteur)
        choix = choisir_fournisseur(crise, demande_jour, ecart_type_jour,
                                    prix_vente).index[0]
        if choix != choix_normal:
            return round(float(facteur), 1), choix
    return None, choix_normal


if __name__ == "__main__":
    demande_jour = 20      # ventes par jour (module 1)
    ecart_type_jour = 6    # variation des ventes par jour

    for prix_vente in [10.0, 20.0]:     # deux produits inventés
        print(f"\n===== Produit vendu {prix_vente:.0f} € =====")

        normal = choisir_fournisseur(FOURNISSEURS_EXEMPLE, demande_jour,
                                     ecart_type_jour, prix_vente)
        normal = rentabilite(normal, demande_jour, prix_vente)
        print("Temps normal :")
        print(normal[["total", "benefice", "rentable"]])

        crise = choisir_fournisseur(scenario_crise(FOURNISSEURS_EXEMPLE, CRISE_REELLE),
                                    demande_jour, ecart_type_jour, prix_vente)
        crise = rentabilite(crise, demande_jour, prix_vente)
        print(f"Crise (retards x{CRISE_REELLE}) :")
        print(crise[["total", "benefice", "rentable"]])

        facteur, nouveau = point_de_bascule(FOURNISSEURS_EXEMPLE, demande_jour,
                                            ecart_type_jour, prix_vente)
        print(f"Choix normal : {normal.index[0]} | choix en crise : {crise.index[0]}")
        if facteur is None:
            print("Point de bascule : aucun (jusqu'à x10)")
        else:
            print(f"Point de bascule : retards x{facteur} -> passer à {nouveau}")