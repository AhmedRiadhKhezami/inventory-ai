import lightgbm as lgb
import mlflow
import pandas as pd

from src.features import (charger_donnees, construire_exercice, construire_entrainement,
                          FEATURES_C, FEATURES_D, FEATURES_E)
from src.metrics import wape, biais

CHEMIN_DONNEES = "data/processed/sales_ca1_clean.parquet"
CHEMIN_SIGNAUX = "data/processed/signaux_externes.parquet"
TESTS = {"Test 1": "2016-02-29", "Test 2": "2016-03-28"}
PARAMS = dict(objective="tweedie", n_estimators=300, learning_rate=0.05, verbose=-1)

EXPERIENCES = {"C": FEATURES_C, "D": FEATURES_D, "E": FEATURES_E}


def entrainer_et_tester(df, debut_test, features, signaux=None):
    """Entraîne le modèle sur le passé, puis le teste sur les 28 jours suivants."""
    train = construire_entrainement(df, debut_test, signaux=signaux)
    test = construire_exercice(df, debut_test, signaux)

    modele = lgb.LGBMRegressor(**PARAMS)
    modele.fit(train[features], train["sales"])
    test["prevu"] = modele.predict(test[features])

    totaux = test.groupby("item_id")[["sales", "prevu"]].sum()
    resultats = {
        "wape_jour": wape(test["sales"], test["prevu"]),
        "wape_28j": wape(totaux["sales"], totaux["prevu"]),
        "biais": biais(test["sales"], test["prevu"]),
    }
    return modele, test, resultats


if __name__ == "__main__":
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("inventory-ai")

    df = charger_donnees(CHEMIN_DONNEES)
    signaux = pd.read_parquet(CHEMIN_SIGNAUX)

    for nom_modele, features in EXPERIENCES.items():
        for nom_test, debut in TESTS.items():
            with mlflow.start_run(run_name=f"{nom_modele} - {nom_test}"):
                _, _, r = entrainer_et_tester(df, debut, features, signaux)

                mlflow.log_params(PARAMS)
                mlflow.log_param("modele", nom_modele)
                mlflow.log_param("test", nom_test)
                mlflow.log_param("debut_test", debut)
                mlflow.log_param("nb_features", len(features))
                mlflow.log_param("features", ",".join(features))
                mlflow.log_metrics(r)

            print(f"Modèle {nom_modele} | {nom_test} | WAPE jour : {r['wape_jour']*100:.1f} % "
                  f"| WAPE 28 j : {r['wape_28j']*100:.1f} % "
                  f"| Biais : {r['biais']*100:+.1f} %")