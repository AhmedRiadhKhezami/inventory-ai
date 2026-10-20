import numpy as np

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


if __name__ == "__main__":
    # Exemple : coques de téléphone, usine en Asie, bateau
    demande_jour = 20        # ventes moyennes par jour (module 1)
    ecart_type_jour = 6      # variation des ventes par jour
    delai_prevu = 35         # délai annoncé par le fournisseur
    marge_p90 = 31           # marge retard Direct + Ocean + Asia (module 2)
    stock_actuel = 900
    en_route = 0
    frais_par_commande = 400 # fret + douane + frais fixes (€)
    prix_achat = 2.0         # prix d'une coque (€)
    moq = 1000               # minimum imposé par l'usine
    carton = 100             # pièces par carton

    commander, seuil = faut_il_commander(stock_actuel, en_route, demande_jour,
                                         ecart_type_jour, delai_prevu, marge_p90)
    print(f"D1 | seuil = {seuil} | stock = {stock_actuel} | commander ? {commander}")

    if commander:
        for nom, plafond in [("Sans plafond", None), ("Plafond 120 jours", 120)]:
            q, eoq, manque = quantite_a_commander(
                stock_actuel + en_route, seuil, demande_jour, frais_par_commande,
                prix_achat, moq=moq, carton=carton, couverture_max_jours=plafond)
            print(f"D2 | {nom:18s} | manque = {manque} | EOQ = {eoq} "
                  f"| à commander = {q} ({q / demande_jour:.0f} jours de ventes)")

    print("\nCoût par an selon la quantité commandée :")
    for q in [500, 1000, 2400, 3400, 7300]:
        c = cout_annuel(q, demande_jour, frais_par_commande, prix_achat)
        print(f"  Q = {q:5d} -> {c:7.0f} €")