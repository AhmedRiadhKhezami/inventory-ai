import lightgbm as lgb

from src.features import charger_donnees, construire_exercice, construire_entrainement, FEATURES
from src.metrics import wape, biais

CHEMIN_DONNEES = "data/processed/sales_ca1_clean.parquet"
TESTS = {"Test 1": "2016-02-29", "Test 2": "2016-03-28"}
PARAMS = dict(objective="tweedie", n_estimators=300, learning_rate=0.05, verbose=-1)


def entrainer_et_tester(df, debut_test):
    """Entraîne le modèle sur le passé, puis le teste sur les 28 jours suivants."""
    train = construire_entrainement(df, debut_test)
    test = construire_exercice(df, debut_test)

    modele = lgb.LGBMRegressor(**PARAMS)
    modele.fit(train[FEATURES], train["sales"])
    test["prevu"] = modele.predict(test[FEATURES])

    totaux = test.groupby("item_id")[["sales", "prevu"]].sum()
    resultats = {
        "wape_jour": wape(test["sales"], test["prevu"]),
        "wape_28j": wape(totaux["sales"], totaux["prevu"]),
        "biais": biais(test["sales"], test["prevu"]),
    }
    return modele, test, resultats


if __name__ == "__main__":
    df = charger_donnees(CHEMIN_DONNEES)
    for nom, debut in TESTS.items():
        _, _, r = entrainer_et_tester(df, debut)
        print(f"{nom} | WAPE jour : {r['wape_jour']*100:.1f} % "
              f"| WAPE 28 j : {r['wape_28j']*100:.1f} % "
              f"| Biais : {r['biais']*100:+.1f} %")