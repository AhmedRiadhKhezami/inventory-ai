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
