# Journal des décisions

## 27/09/2026 : Dataset M5 (Walmart)
- Raison : contient les prix de vente.
- Limite : pas de stock ni de délai fournisseur, à simuler.


## 28/09/2026 : Magasin CA_1 uniquement
- Raison : 3 049 produits, taille réaliste pour une PME.

## 28/09/2026 : Suppression des jours sans prix
- Constat : 19,1 % des lignes (1 129 842) n'ont pas de prix.
- Raison : pas de prix = produit pas encore en magasin.
  Leurs ventes à 0 sont de "faux zéros".
- Action : lignes supprimées. Les vrais 0 (produit en rayon,
  aucune vente) sont gardés.
- Résultat : 5 918 109 → 4 788 267 lignes.

## 28/09/2026 : Format Parquet pour les données propres
- Raison : plus léger et plus rapide que CSV, conserve les types
  (dates), standard Big Data (Spark, Databricks).

  ## 28/09/2026 : Le 25 décembre est un jour anormal
- Constat : chaque 25 décembre, les ventes tombent presque à 0.
- Raison : Walmart ferme le jour de Noël (ce n'est pas une baisse de demande).
- Action prévue : retirer ce jour de l'entraînement, ou ajouter une
  variable "magasin fermé". Décision à prendre lors de la modélisation.