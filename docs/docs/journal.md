# Journal de bord

## 28/09/2026 : Mise en place et préparation des données

### Fait
- Création du dépôt GitHub `inventory-ai` et de la structure des dossiers
- Environnement Python 3.14 (.venv) + bibliothèques installées
- Téléchargement du dataset M5 (Walmart) sur Kaggle
- Chargement des 3 fichiers : ventes (30 490 × 1 947),
  calendrier (1 969 × 14), prix (6 841 121 × 4)
- Filtre sur le magasin CA_1 : 3 049 produits
- Passage du format large au format long (melt) : 5 918 109 lignes
- Ajout de la date et des événements (merge avec le calendrier)
- Ajout du prix (merge sur magasin + produit + semaine)
- Suppression des jours sans prix : 4 788 267 lignes restantes

### Appris
- `melt` : transformer les colonnes de jours en lignes
- `merge` : joindre deux tableaux avec une colonne commune (comme RECHERCHEV)
- Un 0 de vente n'a pas toujours le même sens : il faut vérifier
  si le produit était disponible

### Prochaine étape
- Sauvegarder le tableau propre
- Premiers graphiques des ventes


## 28/09/2026 (suite) : Première analyse des ventes

### Observations (magasin CA_1, ventes totales par jour)
- Tendance : les ventes augmentent de 2011 à 2016
- Chute à presque 0 chaque 25 décembre (magasin fermé)
- Saisonnalité hebdomadaire : plus de ventes le samedi et le dimanche

### Conséquences pour le modèle
- Donner le jour de la semaine au modèle
- Utiliser les ventes de la semaine précédente (même jour)
- Traiter le 25 décembre à part

### Appris
- groupby : regrouper et additionner (total par jour, moyenne par jour de semaine)
- nsmallest : trouver les valeurs les plus basses
- Toujours vérifier une observation visuelle avec des chiffres

### Demande intermittente (analyse par produit)
- 55,2 % des lignes produit × jour sont à 0 vente
- Répartition des 3 049 produits selon leur part de jours à 0 :
  - Quotidien (< 20 %) : 229 (7,5 %)
  - Régulier (20-50 %) : 959 (31,5 %)
  - Irrégulier (50-80 %) : 1 370 (44,9 %)
  - Rare (> 80 %) : 491 (16,1 %)
- 61 % des produits ne se vendent pas la plupart des jours

### Ruptures de stock probables (demande censurée)
- Découverte : des produits avec prix (donc censés être en vente)
  restent des mois à 0, puis se revendent régulièrement.
  Exemples : FOODS_3_261 (~8 mois à 0), HOUSEHOLD_2_398 (~7 mois à 0)
- Plus longue période de jours à 0 d'affilée, par produit :
  - ≥ 60 jours : 1 941 produits (63,7 %), mélange produits rares + ruptures
  - ≥ 180 jours : 628 produits (20,6 %), ruptures ou retraits très probables

  ## 30/09/2026 : Premières méthodes simples (Test 1)

| Méthode | Erreur par jour | Erreur sur 28 jours |
|---|---|---|
| Moyenne 28 derniers jours | 75,3 % | 27,8 % |
| Même jour semaine dernière | 86,9 % | 34,1 % |
| Moyenne même jour sur 8 semaines | 75,6 % | 29,7 % |

- La meilleure : moyenne des 28 derniers jours.
- Un seul jour du passé = trop de hasard → mauvais.
- Sur 28 jours, les erreurs s'équilibrent → 28 % au lieu de 75 %.

### Test 2 (28/03 → 24/04/2016)

| Méthode | Erreur par jour | Erreur sur 28 jours |
|---|---|---|
| Moyenne 28 derniers jours | 74,5 % | 26,8 % |
| Même jour semaine dernière | 88,8 % | 36,2 % |
| Moyenne même jour sur 8 semaines | 75,0 % | 27,1 % |

- Même classement qu'au Test 1 → résultat fiable, pas de la chance.
- Chiffre à battre (moyenne Test 1 + Test 2) : 27,3 % sur 28 jours.

## 30/09/2026 : Premier modèle LightGBM

### Version 1 (indices = ventes d'il y a 28 jours et plus)
| Modèle | Test 1 (28 j) |
|---|---|
| A : ventes passées | 30,6 % |
| B : + prix | 30,2 % |
| C : + calendrier | 30,1 % |
→ Moins bien que la méthode simple (27,8 %).
Cause : les ventes utilisées étaient trop vieilles (1 mois de retard).

### Version 2 ("lundi matin" : on connaît tout jusqu'à la veille)
- 50 exercices dans le passé (un toutes les 2 semaines)
- Indices : moyennes 7/28/56 j, part des jours avec vente,
  moyenne du même jour, horizon (J+1…J+28), prix, calendrier

| | Test 1 (28 j) | Test 2 (28 j) | Moyenne |
|---|---|---|---|
| Méthode simple | 27,8 % | 26,8 % | 27,3 % |
| Modèle C v2 | 27,1 % | 25,9 % | 26,5 % |

→ Le modèle bat la méthode simple sur les 2 périodes. Gain petit (~0,8 point).