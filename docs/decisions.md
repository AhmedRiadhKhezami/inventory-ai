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

  ## 29/09/2026 : Prévision par produit et par jour
- Raison : effet du jour de la semaine + délai fournisseur variable
  selon le produit + possibilité d'additionner pour tout total.
- La décision de commande utilise la somme sur le délai fournisseur.


## 29/09/2026 : Horizon de prévision = 28 jours
- Raison : couvre délai fournisseur + période entre deux commandes.
- Cohérent avec le standard M5 (comparaison possible).

## 29/09/2026 : Validation temporelle sur 3 périodes de 28 jours
- Raison : un découpage au hasard ferait voir le futur au modèle
  (data leakage) et donnerait une note trop optimiste.
- 3 périodes au lieu d'une : éviter un résultat dû à la chance.
- Dernière période réservée au test final (utilisée une seule fois).


## 29/09/2026 : Mesures d'erreur = WAPE + biais
- WAPE : supporte les zéros (contrairement au MAPE).
- Biais : indique le sens de l'erreur (rupture vs surstock).
- Calcul global et par groupe de produits.

## 30/09/2026 : Méthode de référence = moyenne 28 jours
- Erreur par jour : 75,3 %. Erreur sur 28 jours : 27,8 %.
- Le vrai modèle doit faire mieux.
- On mesure les 2 : par jour (pour comparer les modèles)
  et sur 28 jours (c'est ce qui compte pour la commande).

  ## 30/09/2026 : Détecteur de ruptures, version 1 (mis de côté)
- Résultat : 18,4 % des lignes marquées, 97 % des produits → trop.
- Vérification visuelle : bon sur les longues coupures,
  fausses alertes quand le rythme de vente du produit change.
- Amélioration prévue : seuil basé sur le rythme récent (6 mois).
- Mis de côté pour avancer sur LightGBM.


## 30/09/2026 : Construction des données par "date d'origine"
- Problème : avec des indices d'il y a 28 jours et plus, le modèle
  avait moins d'infos récentes que la méthode simple.
- Solution : 50 dates d'origine dans le passé. Pour chacune, indices
  calculés jusqu'à la veille + les 28 jours suivants à prévoir.
- Résultat : le modèle bat la méthode simple (26,5 % contre 27,3 %).


## 01/10/2026 : Le code va dans src/, les notebooks servent à regarder
- Raison : la fonction wape était copiée dans 2 notebooks. Une erreur
  corrigée à un endroit restait à l'autre.
- Règle : chaque fonction est écrite UNE SEULE FOIS dans src/.
  Les notebooks importent ces fonctions pour analyser et faire des graphiques.
- Réglages (chemin, dates des tests, paramètres) en haut de train.py,
  à un seul endroit.