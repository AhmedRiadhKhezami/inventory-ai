import numpy as np

# z = 1.65 -> on veut couvrir 95% des variations de la demande
Z_SERVICE = 1.65


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


if __name__ == "__main__":
    # Exemple : coques de téléphone, usine en Asie, bateau
    demande_jour = 20      # ventes moyennes par jour (module 1)
    ecart_type_jour = 6    # variation des ventes par jour
    delai_prevu = 35       # délai annoncé par le fournisseur
    marge_p90 = 31         # marge retard Direct + Ocean + Asia (module 2)
    stock_actuel = 900

    for nom, marge in [("Sans marge retard", 0), ("Avec marge P90", marge_p90)]:
        decision, seuil = faut_il_commander(stock_actuel, 0, demande_jour,
                                            ecart_type_jour, delai_prevu, marge)
        print(f"{nom:20s} | seuil = {seuil:5d} | stock = {stock_actuel} "
              f"| commander ? {decision}")