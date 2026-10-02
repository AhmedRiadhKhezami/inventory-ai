# Journal de bord

## Mise en place et préparation des données

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


## Première analyse des ventes

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

  ## Premières méthodes simples (Test 1)

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

## Premier modèle LightGBM

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

### Modèle v3 (+ prix relatif, tendance, jours sans vente, rayon, catégorie)
| Erreur sur 28 jours | Test 1 | Test 2 | Moyenne |
|---|---|---|---|
| Méthode simple | 27,8 % | 26,8 % | 27,3 % |
| Modèle v2 | 27,1 % | 25,9 % | 26,5 % |
| Modèle v3 | 26,5 % | 25,7 % | 26,1 % |

### Importance des indices
- Par nombre d'utilisations : prix, jours sans vente, mois, rayon en haut.
- Par GAIN (ce qui réduit vraiment l'erreur) : moy_28j >> moy_56j > moy_7j
  > moy_meme_jour. Tout le reste aide peu.
- Le prix est souvent utilisé mais aide peu : il sert surtout à
  reconnaître le produit.
- Conclusion : le modèle = surtout "moyenne récente + petites corrections".

## Phase 3, code propre (début)

### Fait
- src/metrics.py : fonctions wape et biais (testées : 25 % / +5 % sur l'exemple)
- src/features.py : charger_donnees, construire_exercice ("lundi matin"),
  construire_entrainement (50 lundis), liste FEATURES (16 indices)
- src/train.py : entraîne et teste le modèle sur Test 1 et Test 2
- Une seule commande lance tout : .venv\Scripts\python -m src.train

### Vérification
- Mêmes résultats que le notebook 05 (v3) :
  Test 1 = 26,5 %, Test 2 = 25,7 % (WAPE 28 jours)
  → le déplacement du code n'a rien cassé

### Appris
- sys.path.append("..") pour importer src/ depuis un notebook
- if __name__ == "__main__" : code lancé seulement quand on exécute le fichier
- Toujours vérifier qu'on retrouve les mêmes chiffres après avoir déplacé du code

## MLflow
- Installation de MLflow, résultats enregistrés dans mlflow.db
- train.py enregistre pour chaque essai : paramètres, nom du modèle,
  période de test, liste des indices, WAPE jour, WAPE 28 j, biais
- Premier essai enregistré : v3 (Test 1 = 26,5 %, Test 2 = 25,7 %)
- Page web : mlflow ui --backend-store-uri sqlite:///mlflow.db

## MLflow
- Installation de MLflow 3.16.1, résultats enregistrés dans mlflow.db
- train.py enregistre pour chaque essai : paramètres, nom du modèle,
  période de test, liste des indices, WAPE jour, WAPE 28 j, biais
- Premier essai enregistré : v3 (Test 1 = 26,5 %, Test 2 = 25,7 %)
- Page web : mlflow ui --backend-store-uri sqlite:///mlflow.db
  puis http://127.0.0.1:5000


  ## Tests automatiques (fin de la Phase 3)
- pytest installé
- tests/test_metrics.py : 3 tests (WAPE, biais, prévision parfaite)
- tests/test_features.py : 3 tests (28 jours, moyenne 7 jours,
  pas de triche avec le futur)
- Commande : .venv\Scripts\python -m pytest -v → 6 passed
- Phase 3 terminée : code dans src/, MLflow, tests

## Phase 4.1 : Téléchargement des signaux économiques (FRED)
- src/external.py télécharge 5 signaux depuis FRED :
  pétrole (DCOILWTICO, jour), essence (GASREGW, semaine),
  inflation (CPIAUCSL, mois), confiance (UMCSENT, mois),
  dollar (DTWEXBGS, jour)
- Fichiers rangés dans data/raw/external/ (pas sur GitHub)
- Commande : .venv\Scripts\python -m src.external

## Phase 4.1 : Téléchargement des signaux économiques (FRED)
- src/external.py télécharge 5 signaux depuis FRED
- Résultat :
  - pétrole : 10 629 lignes (par jour ouvré, depuis 1986)
  - essence : 1 885 lignes (par semaine, depuis 1990)
  - inflation : 956 lignes (par mois, depuis 1947)
  - confiance : 886 lignes (par mois, depuis 1952)
  - dollar : 5 410 lignes (par jour ouvré, depuis 2006)
- Tous commencent avant 2011 → utilisables avec M5
- À faire : les mettre tous au rythme "par jour" (étape 4.3)

## Phase 4.2 : Signaux géopolitiques (GPR) et logistiques (GSCPI)
- Téléchargés à la main (pas de téléchargement automatique simple) :
  - data_gpr_export.xls (GPR par mois, depuis 1985, dont GPRC_USA)
  - data_gpr_daily_recent.xls (GPR par jour, depuis 1985, moyennes 7 et 30 j)
  - gscpi_data.xls (GSCPI par mois, depuis 1998, onglet "GSCPI Monthly Data")
- src/external.py lit ces fichiers et les sauvegarde en CSV propres :
  gpr_mois.csv, gpr_jour.csv, gscpi.csv
- Vérification : GPR de mars 2011 = 136,9 (Libye, Fukushima) contre
  79,4 en janvier → l'indice réagit aux vrais événements

  ## Phase 4.3 : Table des signaux externes par jour
- src/signaux.py : 1 ligne par jour (2009 → 2016), 11 signaux + 3 variations
  (pétrole sur 30 j, essence sur 30 j, inflation sur 12 mois)
- Chaque signal = la dernière valeur DÉJÀ CONNUE ce jour-là
  (délai de publication + merge_asof)
- Sauvegardé dans data/processed/signaux_externes.parquet
- Commande : .venv\Scripts\python -m src.signaux


## Changement de direction : projet "import / e-commerce"
- M5 abandonné : supermarché, pas d'import, signaux externes inutiles.
- Nouveau projet en 3 modules :
  1. Délais d'import → données USAID (vrais envois internationaux)
  2. Demande → Online Retail II (vrai e-commerce)
  3. Décision → quand et combien commander, selon l'origine

## Module 1 : Préparation des données USAID
- 10 324 envois (2006-2015), surtout vers l'Afrique
- Texte réparé avec ftfy (ex : "CÃ´te" → "Côte d'Ivoire")
- Pays d'origine trouvé à partir du nom de l'usine (88 usines,
  4 inconnues → 17 envois sans pays)
- Nouvelles colonnes : pays_origine, region_origine, retard_jours,
  en_retard, delai_total_jours
- Commande : .venv\Scripts\python -m src.usaid

### Premiers résultats
| Région d'origine | Envois | % en retard |
|---|---|---|
| Asie | 8 214 | 13,9 % |
| Europe | 1 636 | 2,4 % |
| Afrique | 184 | 1,1 % |
| Amérique | 271 | 0,7 % |

| Transport | % en retard |
|---|---|
| Bateau | 17,5 % |
| Camion | 16,1 % |
| Avion affrété | 11,5 % |
| Avion | 9,6 % |

- Attention : lien ≠ cause (l'Asie = surtout génériques indiens).


## Module 1 : Retards dans le temps et pression logistique (GSCPI)
- Notebook 06_usaid_analyse

| Années | Envois par an | % en retard |
|---|---|---|
| 2006 | 65 | 0 % |
| 2007-2009 | 672 à 1 253 | 1,3 à 3,6 % |
| 2010-2015 | 1 011 à 1 528 | 7,9 à 23,5 % |

- Saut brutal en 2010 : retards probablement mal enregistrés avant.
- Corrélation % de retard / GSCPI (par mois) :
  - toutes années : 0,32
  - depuis 2010 : 0,45
- Pic commun en 2010-2011 (GSCPI ≈ +1,6 début 2011, retards > 50 %),
  période du tremblement de terre au Japon.
- Ensuite (2012-2015) : GSCPI bas, retards variables sans lien clair.


## Module 1 : Informations disponibles au moment de la commande
- 7 305 envois depuis 2010
- Fulfill Via :
  - Direct Drop (direct de l'usine) : 3 697 envois, 6,2 % en retard
  - From RDC (entrepôt régional) : 3 608 envois, 24,5 % en retard
- Produits : ARV (6 143), HRDT (1 137), autres très rares
- 40 pays de destination, 55 fournisseurs
- Bug corrigé : la date de commande est écrite "8/27/14" (mois/jour/année),
  les autres dates "14-Nov-06". lire_date lit maintenant les 2 formats.
  Date de commande manquante : 100 % → 50,2 %
  (= envois From RDC, sans commande fournisseur, + "Date Not Captured")

  ## Module 1 : Baseline du modèle de retard
- Règle : risque = % de retard du passé pour la même combinaison
  (usine/entrepôt + transport + région d'origine)
- Alerte si risque > moyenne du passé

| Test | Retards réels | AUC | Rappel | Précision | Alertes |
|---|---|---|---|---|---|
| Test 1 (2013) | 17,9 % | 0,669 | 75,0 % | 28,0 % | 48,0 % |
| Test 2 (2014) | 15,4 % | 0,818 | 90,3 % | 34,4 % | 40,6 % |

- AUC moyenne à battre : 0,744
- Défaut : trop d'alertes (~45 % des envois), 2 alertes sur 3 fausses
- Commande : .venv\Scripts\python -m src.retard


## Module 1 : LightGBM R1 (sans signaux externes)
- 18 informations connues à la commande (origine, destination,
  transport, produit, quantité, prix, délai prévu, mois...)
- Réglages prudents (peu de données) : num_leaves=15, min_child_samples=30

| Modèle | AUC Test 1 | AUC Test 2 | AUC moyenne |
|---|---|---|---|
| Baseline | 0,669 | 0,818 | 0,744 |
| R1 | 0,713 | 0,813 | 0,763 |

- R1 donne moins d'alertes (31 % et 29 % au lieu de 48 % et 41 %),
  donc rappel plus bas : comparaison du rappel non juste (seuils différents).
- Essais enregistrés dans MLflow (expérience "retard-import").


## Module 1 : Diagnostic de R1 + indices historiques (R1B)
### Diagnostic (Test 2)
- AUC usine (Direct Drop) : 0,829. AUC entrepôt (From RDC) : 0,494 = hasard.
- L'AUC globale vient surtout de "entrepôt = risqué, usine = sûr".
- Importance : Vendor 22 % (contient l'info usine/entrepôt), pays de
  destination 15 %, prix et quantités élevés, origine 0 %.

### R1B = R1 + 5 indices historiques
(% de retard récent : global, pays, fournisseur, mode + charge du pays ;
fenêtre de 180 jours, décision 30 jours avant la date prévue)

| Modèle | AUC T1 | AUC T2 | Moyenne | Entrepôt T1 | Entrepôt T2 |
|---|---|---|---|---|---|
| Baseline | 0,669 | 0,818 | 0,744 | 0,532 | 0,566 |
| R1 | 0,713 | 0,813 | 0,763 | 0,503 | 0,494 |
| R1B | 0,753 | 0,821 | 0,787 | 0,608 | 0,511 |

- L'historique aide au global et pour les entrepôts en 2013, pas en 2014.
- AUC usine 2014 peu fiable : seulement ~18 retards.

## Module 1 : Recherche d'amélioration du modèle de retard (20+ essais)
Évalués sur 2012, 2013, 2014 (moyenne 2013-2014)

| Idée | AUC moyenne |
|---|---|
| Baseline | 0,744 |
| R1 | 0,763 |
| + historique 6 mois | 0,787 |
| + historique 2 mois et 6 mois (R2) | 0,798 ← meilleur |
| + charge prévue (même jour, fin de mois) | 0,761 |
| + envois déjà en retard à la décision | 0,776 |
| + signaux externes | 0,764 |
| 2 modèles séparés usine/entrepôt | 0,802 (pas stable) |
| Modèle plus prudent + poids récents | 0,789 |
| Cible "gros retards" (> 7 ou > 14 jours) | 0,72 à 0,78 |

### Découvertes
- Entrepôts 2013-2014 : 1 294 lignes mais 443 envois réels (date + pays) ;
  88 % des lignes d'un même envoi ont le même résultat.
- Test "triche" (vrai % de retard du même mois) : AUC entrepôt = 0,65 seulement.
  Il faut "même mois ET même pays" pour 0,81 → causes non présentes
  dans les données (stock d'entrepôt, incidents de transport).
- Signaux externes : liés aux retards par mois, mais déjà contenus dans
  le % de retard des 2 derniers mois → pas de gain pour le modèle.