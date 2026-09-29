# Cadrage du problème de prévision

## Objectif business
Aider un commerçant à savoir quoi commander, combien, et quand,
pour éviter les ruptures de stock sans immobiliser trop d'argent.

## 1. On prévoit quoi ?
Les ventes de chaque produit, pour chaque jour (magasin CA_1).

Pourquoi jour par jour :
- le jour de la semaine influence fortement les ventes (week-end)
- le délai fournisseur varie selon le produit : on additionne
  le nombre de jours nécessaire pour chacun
- à partir du détail par jour, on peut calculer n'importe quel
  total ; l'inverse est impossible

Utilisation : pour la décision de commande, on additionne les
prévisions sur la durée du délai fournisseur.

## 2. Sur combien de jours à l'avance ?
28 jours.

Pourquoi : une commande doit couvrir le délai fournisseur
+ la période jusqu'à la livraison suivante.
Exemple : délai de 14 jours + commande toutes les 2 semaines
= 28 jours à couvrir.

La vitesse de vente du produit ne change pas l'horizon :
elle change la QUANTITÉ à commander.

Bonus : 28 jours est aussi l'horizon officiel de la
compétition M5, ce qui permet de comparer les résultats.


## 3. Comment on vérifie ?
Découpage TEMPOREL : le test est toujours APRÈS l'entraînement.
Jamais de découpage au hasard (le modèle verrait le futur :
fuite de données / data leakage).

Backtest sur 3 périodes de 28 jours :
- Test 1 : entraînement jusqu'au 28/02/2016 → prévision du 29/02 au 27/03/2016
- Test 2 : entraînement jusqu'au 27/03/2016 → prévision du 28/03 au 24/04/2016
- Test 3 : entraînement jusqu'au 24/04/2016 → prévision du 25/04 au 22/05/2016

Règle :
- Tests 1 et 2 : pour comparer et améliorer les modèles
- Test 3 : gardé de côté, utilisé UNE SEULE FOIS à la fin
  pour le résultat final du rapport


  ## 4. Avec quelle mesure d'erreur ?
Mesure principale : WAPE
WAPE = somme des |vrai - prévu| ÷ somme des vraies ventes
→ "sur 100 unités vendues, de combien le modèle se trompe"

Pourquoi pas le MAPE : il divise par la vraie vente de chaque
jour → impossible quand elle vaut 0 (55 % des lignes).

Mesure complémentaire : le biais
Biais = (total prévu - total réel) ÷ total réel
- biais négatif → sous-estimation → risque de rupture
- biais positif → surestimation → argent bloqué en stock

Les deux mesures sont calculées au global ET par groupe de
produits (Quotidien, Régulier, Irrégulier, Rare).