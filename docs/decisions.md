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

  ## 28/09/2026 : Pas de MAPE, utilisation du WAPE / MAE
- Raison : 55,2 % des ventes sont à 0 → le MAPE divise par 0.

## 28/09/2026 : Prévoir sur la période du délai fournisseur
- Raison : pour 61 % des produits, le jour exact de vente est
  imprévisible. La commande dépend du total sur le délai
  fournisseur, qui est plus stable à prévoir.

## 28/09/2026 : Évaluer l'erreur par groupe de produits
- Raison : les produits rares et quotidiens n'ont pas le même
  comportement, une erreur globale peut cacher des problèmes.

  ## 29/09/2026 : Détection des ruptures probables (à implémenter)
- Constat : de longues périodes à 0 avec prix = probablement rupture
  de stock ou retrait du rayon, pas absence de demande.
- Risque : le modèle sous-estime la demande → commandes trop faibles
  → encore plus de ruptures.
- Méthode prévue : seuil RELATIF au rythme de vente du produit
  (pas un nombre de jours fixe, qui confondrait produits rares et ruptures).
- Options : retirer ces périodes de l'entraînement, ou les marquer
  avec une variable "rupture_probable".