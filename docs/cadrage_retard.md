# Cadrage : modèle de retard d'import (USAID)

## Question
Au moment de la commande, cet envoi va-t-il arriver en retard ?
Sortie : un risque entre 0 et 100 %.

## Données
USAID, envois de 2010 à 2015 (7 305 envois).
Cible : en_retard = 1 si date réelle > date prévue, sinon 0.

## Informations autorisées (connues à la commande)
Origine, usine, fournisseur, destination, transport prévu, Fulfill Via
(usine ou entrepôt), type de produit, quantité, date prévue,
signaux externes déjà publiés.

## Vérification dans le temps
- Test 1 : apprend 2010-2012 → testé sur 2013
- Test 2 : apprend 2010-2013 → testé sur 2014
- Test final : apprend 2010-2014 → testé sur 2015 (UNE SEULE FOIS)

## Mesures
- AUC (principale) : le modèle classe-t-il les envois risqués avant
  les envois sûrs ? 0,5 = hasard, 1 = parfait.
- Rappel : part des vrais retards trouvés.
- Précision : part des alertes qui sont de vrais retards.
- Pas de "% de bonnes réponses" : un modèle qui dit toujours "à l'heure"
  aurait ~85 % sans trouver aucun retard.