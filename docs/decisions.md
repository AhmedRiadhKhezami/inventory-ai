# Journal des décisions

## Dataset M5 (Walmart)
- Raison : contient les prix de vente.
- Limite : pas de stock ni de délai fournisseur, à simuler.


## Magasin CA_1 uniquement
- Raison : 3 049 produits, taille réaliste pour une PME.

## Suppression des jours sans prix
- Constat : 19,1 % des lignes (1 129 842) n'ont pas de prix.
- Raison : pas de prix = produit pas encore en magasin.
  Leurs ventes à 0 sont de "faux zéros".
- Action : lignes supprimées. Les vrais 0 (produit en rayon,
  aucune vente) sont gardés.
- Résultat : 5 918 109 → 4 788 267 lignes.

## Format Parquet pour les données propres
- Raison : plus léger et plus rapide que CSV, conserve les types
  (dates), standard Big Data (Spark, Databricks).

  ## Le 25 décembre est un jour anormal
- Constat : chaque 25 décembre, les ventes tombent presque à 0.
- Raison : Walmart ferme le jour de Noël (ce n'est pas une baisse de demande).
- Action prévue : retirer ce jour de l'entraînement, ou ajouter une
  variable "magasin fermé". Décision à prendre lors de la modélisation.

  ## Pas de MAPE, utilisation du WAPE / MAE
- Raison : 55,2 % des ventes sont à 0 → le MAPE divise par 0.

## Prévoir sur la période du délai fournisseur
- Raison : pour 61 % des produits, le jour exact de vente est
  imprévisible. La commande dépend du total sur le délai
  fournisseur, qui est plus stable à prévoir.

## Évaluer l'erreur par groupe de produits
- Raison : les produits rares et quotidiens n'ont pas le même
  comportement, une erreur globale peut cacher des problèmes.

  ## Détection des ruptures probables (à implémenter)
- Constat : de longues périodes à 0 avec prix = probablement rupture
  de stock ou retrait du rayon, pas absence de demande.
- Risque : le modèle sous-estime la demande → commandes trop faibles
  → encore plus de ruptures.
- Méthode prévue : seuil RELATIF au rythme de vente du produit
  (pas un nombre de jours fixe, qui confondrait produits rares et ruptures).
- Options : retirer ces périodes de l'entraînement, ou les marquer
  avec une variable "rupture_probable".

  ## Prévision par produit et par jour
- Raison : effet du jour de la semaine + délai fournisseur variable
  selon le produit + possibilité d'additionner pour tout total.
- La décision de commande utilise la somme sur le délai fournisseur.


## Horizon de prévision = 28 jours
- Raison : couvre délai fournisseur + période entre deux commandes.
- Cohérent avec le standard M5 (comparaison possible).

## Validation temporelle sur 3 périodes de 28 jours
- Raison : un découpage au hasard ferait voir le futur au modèle
  (data leakage) et donnerait une note trop optimiste.
- 3 périodes au lieu d'une : éviter un résultat dû à la chance.
- Dernière période réservée au test final (utilisée une seule fois).

## Mesures d'erreur = WAPE + biais
- WAPE : supporte les zéros (contrairement au MAPE).
- Biais : indique le sens de l'erreur (rupture vs surstock).
- Calcul global et par groupe de produits.

## Méthode de référence = moyenne 28 jours
- Erreur par jour : 75,3 %. Erreur sur 28 jours : 27,8 %.
- Le vrai modèle doit faire mieux.
- On mesure les 2 : par jour (pour comparer les modèles)
  et sur 28 jours (c'est ce qui compte pour la commande).

  ## Détecteur de ruptures, version 1 (mis de côté)
- Résultat : 18,4 % des lignes marquées, 97 % des produits → trop.
- Vérification visuelle : bon sur les longues coupures,
  fausses alertes quand le rythme de vente du produit change.
- Amélioration prévue : seuil basé sur le rythme récent (6 mois).
- Mis de côté pour avancer sur LightGBM.

## Construction des données par "date d'origine"
- Problème : avec des indices d'il y a 28 jours et plus, le modèle
  avait moins d'infos récentes que la méthode simple.
- Solution : 50 dates d'origine dans le passé. Pour chacune, indices
  calculés jusqu'à la veille + les 28 jours suivants à prévoir.
- Résultat : le modèle bat la méthode simple (26,5 % contre 27,3 %).

## Le code va dans src/, les notebooks servent à regarder
- Raison : la fonction wape était copiée dans 2 notebooks. Une erreur
  corrigée à un endroit restait à l'autre.
- Règle : chaque fonction est écrite UNE SEULE FOIS dans src/.
  Les notebooks importent ces fonctions pour analyser et faire des graphiques.
- Réglages (chemin, dates des tests, paramètres) en haut de train.py,
  à un seul endroit.

  ## Suivi des essais avec MLflow
- Raison : beaucoup d'essais à venir (C, D, E, réglages). Il faut savoir
  quel réglage a donné quel résultat, sans le noter à la main.
- mlflow.db n'est pas envoyé sur GitHub (.gitignore).

## Suivi des essais avec MLflow
- Raison : beaucoup d'essais à venir (C, D, E, réglages). Il faut savoir
  quel réglage a donné quel résultat, sans le noter à la main.
- mlflow.db n'est pas envoyé sur GitHub (.gitignore).


## Test anti-fuite de données
- Le test change toutes les ventes futures, puis vérifie que les
  indices ne changent pas.
- Raison : la fuite de données (le modèle voit le futur) est l'erreur
  la plus grave en prévision, et elle est invisible dans les résultats.

  ## Signaux économiques choisis (FRED)
- Pétrole et essence : coût de la vie et budget des clients Walmart.
  Il y a un vrai choc dans la période M5 (chute du pétrole en 2014-2015).
- Inflation et confiance : pouvoir d'achat et moral des consommateurs.
- Dollar : prix des produits importés (effet attendu faible).
- Source gratuite, téléchargement automatique, disponible avant 2011.

## Signaux économiques choisis (FRED)
- Pétrole et essence : coût de la vie et budget des clients Walmart.
  Vrai choc dans la période M5 (chute du pétrole en 2014-2015).
- Inflation et confiance : pouvoir d'achat et moral des consommateurs.
- Dollar : prix des produits importés (effet attendu faible).
- Source gratuite, téléchargement automatique, disponible avant 2011.

## Signaux géopolitiques et logistiques
- GPR monde + GPR États-Unis (GPRC_USA) : Walmart est aux États-Unis.
- GPR par jour : utilisé en moyennes 7 et 30 jours, car la valeur
  d'un seul jour varie trop.
- GSCPI : pression sur la logistique mondiale (transport, délais).
- ⚠ Le GSCPI est corrigé après publication (ex : juillet 2026 annoncé
  à 0,79 puis corrigé à 0,94). On utilise les valeurs corrigées,
  qui n'étaient pas connues à l'époque : limite à signaler.

  ## Délais de publication des signaux (anti-triche)
- Un chiffre n'est pas connu le jour qu'il décrit. Ex : l'inflation de
  janvier est publiée vers le 15 février.
- Délais utilisés : 1 jour (pétrole, essence, dollar, GPR jour),
  31 jours (confiance, GPR mois), 38 jours (GSCPI), 45 jours (inflation).
- Pour chaque jour, on prend la dernière valeur dont la date de
  publication est passée (merge_asof "backward").
- Limite : délais approximatifs, et les valeurs ont pu être corrigées
  après publication.


  ## Changement de données : USAID + Online Retail II
- M5 : supermarché sans import. Les signaux externes n'y aidaient pas.
- Le but du projet est l'e-commerce qui importe de plusieurs pays.
- Pas de données publiques réelles d'un e-commerçant importateur.
- USAID : vrais envois internationaux avec pays d'origine, transport,
  date prévue et date réelle. Limite : médicaments, surtout d'Inde,
  surtout en avion.
- Online Retail II : vraies ventes d'une boutique en ligne.
- Le code M5 (pipeline, tests, MLflow, signaux) est réutilisé.

## Pays d'origine à partir du nom de l'usine
- Le fichier n'a pas de colonne "pays d'origine".
- Table usine → pays faite à la main (88 usines).
- 5 usines incertaines, marquées "à vérifier" (peu d'envois).

## Réparation du texte avec ftfy
- Le CSV et l'Excel ont le même texte abîmé (problème à la source).

## Entraînement du modèle de retard à partir de 2010
- 2007-2009 : beaucoup d'envois mais presque aucun retard, puis saut
  brutal en 2010 → enregistrement des retards douteux avant 2010.
- On garde 2010-2015 : 7 305 envois.
- Preuve : la corrélation retard / GSCPI passe de 0,32 à 0,45.

## Les signaux externes jouent sur l'approvisionnement
- M5 (demande en supermarché) : aucun effet.
- USAID (envois internationaux) : lien mesurable avec le GSCPI.
- Le GSCPI sera un indice du modèle de retard, et la base du stress test.


## Indices du modèle de retard : seulement ce qui est connu à la commande
- Autorisé : origine, usine, fournisseur, destination, transport prévu,
  type de produit, quantité, date prévue, signaux déjà publiés.
- Interdit : date réelle de livraison, nombre de jours de retard,
  date d'enregistrement de la livraison.

## From RDC : beaucoup plus de retards (24,5 % contre 6,2 %)
- Surprenant (l'entrepôt est plus proche du client).
- Hypothèses : dates promises trop serrées, ou stock absent de l'entrepôt.
- Indice très fort pour le modèle, à discuter dans le mémoire.

## Mesures du modèle de retard : AUC, rappel, précision
- Seulement ~15 % des envois sont en retard : le "% de bonnes réponses"
  est trompeur (un modèle qui dit toujours "à l'heure" aurait ~85 %).
- AUC = mesure principale. Rappel et précision = lecture business
  (retards ratés → ruptures ; fausses alertes → argent bloqué).

  ## Baseline du modèle de retard
- % de retard historique par combinaison usine/entrepôt + transport
  + région d'origine. Moyenne générale si combinaison inconnue.
- Seuil d'alerte = taux moyen de retard du passé.
- Objectif du vrai modèle : AUC > 0,744 et moins de fausses alertes.


## Comparer les modèles de retard avec l'AUC
- Le rappel et la précision dépendent du seuil d'alerte (la "sensibilité").
- Avec le même seuil, deux modèles ne donnent pas le même nombre
  d'alertes : comparer leur rappel n'est pas juste.
- L'AUC compare les modèles pour tous les seuils.
- Le seuil sera choisi dans le moteur de décision, selon le coût
  d'un retard raté contre le coût d'une fausse alerte.

## Pas de coût de transport, assurance ni poids dans le modèle
- Souvent connus seulement après l'envoi → risque de triche.

## Indices historiques (mémoire du passé récent)
- % de retard récent par pays, fournisseur, mode, global + charge du pays.
- Calculés uniquement avec les envois DÉJÀ LIVRÉS à la date de décision.
- Hypothèse : décision prise 30 jours avant la date de livraison prévue.

## Suivre l'AUC séparément pour usine et entrepôt
- L'AUC globale cache que le modèle ne sait rien faire pour les
  entrepôts (AUC ≈ 0,5). On suit les deux à chaque essai.

## Chemins des fichiers à partir de la racine du projet
- RACINE = Path(__file__).resolve().parent.parent
- Le code marche depuis le terminal ET depuis les notebooks.

## Modèle de retard retenu : R2
- R2 = R1 + historique de retard sur 60 et 180 jours.
- AUC moyenne 0,798 contre 0,744 (baseline) : +7 %.
- Entrepôts : plafond ≈ 0,58, prouvé comme limite des données
  (test "triche" à 0,65), pas comme limite du modèle.

## Rôle des signaux externes dans le module retard
- Pas d'apport en prévision quand l'historique récent est disponible.
- Utiles pour : stress test (scénarios de crise) et nouveau commerçant
  sans historique.

  ## Tester l'historique contre la triche
- Les indices historiques sont la partie la plus risquée du modèle de
  retard : une erreur de signe (< au lieu de <=) ferait voir le futur
  sans que les résultats le montrent.


  ## Marge de retard : méthode simple par groupe
- Plus petite erreur et ~90 % des envois couverts, comme promis.
- LightGBM ne fait pas mieux (82 % seulement en 2013).
- Règle : on garde ce qui marche le mieux, pas le plus compliqué.


## Module 3 – D1 : point de commande avec marge de retard

- **Choix :** ajouter la marge de retard P90 (module 2) au délai prévu dans le point de commande.
- **Pourquoi :** le délai annoncé par le fournisseur est souvent dépassé ; sans marge, l'outil recommande d'attendre alors que la rupture est probable.
- **Choix :** niveau de service 95 % (z = 1.65) pour le stock de sécurité.
- **Pourquoi :** valeur classique en gestion de stock, simple à expliquer ; pourra être réglée par le commerçant plus tard.
- **Alternative écartée :** utiliser seulement le délai prévu (méthode classique) → sous-estime le risque pour les routes lentes comme Asie + bateau.