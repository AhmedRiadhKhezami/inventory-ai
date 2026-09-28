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