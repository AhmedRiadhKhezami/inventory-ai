import pandas as pd

from src.retard import ajouter_historique


def faux_envois():
    """5 envois vers le même pays. Le dernier a sa décision le 02/05/2013
    (= date prévue 01/06/2013 - 30 jours)."""
    return pd.DataFrame({
        "date_prevue": pd.to_datetime(["2013-01-10", "2013-02-10", "2013-03-10",
                                       "2013-05-15", "2013-06-01"]),
        "date_reelle": pd.to_datetime(["2013-01-12", "2013-02-09", "2013-03-20",
                                       "2013-05-20", "2013-06-05"]),
        "en_retard": [1, 0, 1, 1, 1],
        "Country": ["Nigeria"] * 5,
        "Vendor": ["V"] * 5,
        "Fulfill Via": ["From RDC"] * 5,
    })


def test_historique_utilise_seulement_les_envois_deja_arrives():
    df = ajouter_historique(faux_envois(), fenetre=180, suffixe="_180")
    # Arrivés avant le 02/05/2013 : les envois 1, 2 et 3 → 2 retards sur 3
    assert round(df.loc[4, "hist_retard_global_180"], 3) == round(2 / 3, 3)


def test_historique_ne_change_pas_si_le_futur_change():
    df1 = ajouter_historique(faux_envois(), fenetre=180, suffixe="_180")

    futur_change = faux_envois()
    futur_change.loc[3:4, "en_retard"] = 0  # arrivés APRÈS le 02/05 → inconnus
    df2 = ajouter_historique(futur_change, fenetre=180, suffixe="_180")

    assert df1.loc[4, "hist_retard_global_180"] == df2.loc[4, "hist_retard_global_180"]