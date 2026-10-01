import pandas as pd

from src.features import construire_exercice


def faux_tableau():
    """Un faux produit sur 100 jours. Ventes : 0, 1, 2, 3… 99."""
    dates = pd.date_range("2016-01-01", periods=100)
    df = pd.DataFrame({
        "item_id": "A", "dept_id": "FOODS_1", "cat_id": "FOODS",
        "date": dates, "sales": range(100), "sell_price": 2.0, "snap_CA": 0,
    })
    df["jour_semaine"] = df["date"].dt.dayofweek
    df["mois"] = df["date"].dt.month
    df["evenement"] = 0
    return df


def test_28_jours_a_prevoir():
    ex = construire_exercice(faux_tableau(), "2016-03-01")
    assert len(ex) == 28
    assert list(ex["horizon"]) == list(range(1, 29))


def test_moyenne_7j_utilise_seulement_le_passe():
    # Le 01/03/2016 est le jour n°60. Les 7 jours avant ont les ventes 53 à 59.
    ex = construire_exercice(faux_tableau(), "2016-03-01")
    assert ex["moy_7j"].iloc[0] == 56.0


def test_pas_de_triche_avec_le_futur():
    df = faux_tableau()
    df_futur_change = df.copy()
    futur = df_futur_change["date"] >= "2016-03-01"
    df_futur_change.loc[futur, "sales"] = 1000

    ex1 = construire_exercice(df, "2016-03-01")
    ex2 = construire_exercice(df_futur_change, "2016-03-01")

    for col in ["moy_7j", "moy_28j", "moy_56j", "part_jours_vente", "moy_meme_jour"]:
        assert (ex1[col] == ex2[col]).all()