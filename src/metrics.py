import numpy as np


def wape(vrai, prevu):
    """Erreur totale divisée par les ventes totales.
    Exemple : 0.25 = on se trompe de 25 unités pour 100 vendues."""
    vrai = np.asarray(vrai, dtype=float)
    prevu = np.asarray(prevu, dtype=float)
    return np.abs(vrai - prevu).sum() / vrai.sum()


def biais(vrai, prevu):
    """Positif = on prévoit trop. Négatif = on prévoit trop peu."""
    vrai = np.asarray(vrai, dtype=float)
    prevu = np.asarray(prevu, dtype=float)
    return (prevu.sum() - vrai.sum()) / vrai.sum()
    