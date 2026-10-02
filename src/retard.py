import lightgbm as lgb
import mlflow
import pandas as pd
from sklearn.metrics import roc_auc_score, precision_score, recall_score

CHEMIN = "data/processed/usaid_clean.parquet"
TESTS = {"Test 1": 2013, "Test 2": 2014}
GROUPE = ["Fulfill Via", "Shipment Mode", "region_origine"]

CATEGORIES = [
    "Fulfill Via", "Shipment Mode", "region_origine", "pays_origine",
    "Country", "Vendor", "Product Group", "Sub Classification",
    "Vendor INCO Term", "Managed By", "Dosage Form", "First Line Designation",
]
NUMERIQUES = [
    "Line Item Quantity", "Line Item Value", "Pack Price", "Unit Price",
    "delai_prevu_jours", "mois_prevu",
]
FEATURES_R1 = CATEGORIES + NUMERIQUES

PARAMS = dict(n_estimators=300, learning_rate=0.03, num_leaves=15,
              min_child_samples=30, verbose=-1)


def charger():
    """Envois depuis 2010, avec les informations connues à la commande."""
    df = pd.read_parquet(CHEMIN)
    df = df.dropna(subset=["date_prevue"])
    df = df[df["date_prevue"] >= "2010-01-01"].copy()
    df["annee"] = df["date_prevue"].dt.year
    df["region_origine"] = df["region_origine"].fillna("Inconnue")
    df["pays_origine"] = df["pays_origine"].fillna("Inconnu")

    df["delai_prevu_jours"] = (df["date_prevue"] - df["date_commande"]).dt.days
    df["mois_prevu"] = df["date_prevue"].dt.month

    for col in NUMERIQUES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in CATEGORIES:
        df[col] = df[col].fillna("Inconnu").astype("category")
    return df


def mesurer(vrai, risque, seuil):
    """AUC, rappel, précision, et % d'envois qui reçoivent une alerte."""
    alerte = (risque >= seuil).astype(int)
    return {
        "auc": roc_auc_score(vrai, risque),
        "rappel": recall_score(vrai, alerte, zero_division=0),
        "precision": precision_score(vrai, alerte, zero_division=0),
        "pct_alertes": alerte.mean(),
    }


def baseline(train, test):
    """Risque = % de retard du passé pour la même combinaison
    (usine/entrepôt + transport + région d'origine)."""
    taux = (train.groupby(GROUPE, observed=True)["en_retard"].mean()
                 .rename("risque").reset_index())
    t = test.merge(taux, on=GROUPE, how="left")
    t["risque"] = t["risque"].fillna(train["en_retard"].mean())
    return t["risque"].to_numpy()


def modele_lgbm(train, test, features):
    """LightGBM : apprend sur le passé, donne un risque de retard pour le test."""
    m = lgb.LGBMClassifier(**PARAMS)
    m.fit(train[features], train["en_retard"])
    return m.predict_proba(test[features])[:, 1], m


def afficher(nom_modele, nom_test, r):
    print(f"{nom_modele:9} | {nom_test} | AUC : {r['auc']:.3f} "
          f"| Rappel : {r['rappel']*100:.1f} % | Précision : {r['precision']*100:.1f} % "
          f"| Alertes : {r['pct_alertes']*100:.1f} %")


if __name__ == "__main__":
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("retard-import")

    df = charger()
    for nom_test, annee in TESTS.items():
        train = df[df["annee"] < annee]
        test = df[df["annee"] == annee]
        seuil = train["en_retard"].mean()

        # Baseline
        r = mesurer(test["en_retard"], baseline(train, test), seuil)
        afficher("Baseline", nom_test, r)

        # LightGBM R1
        with mlflow.start_run(run_name=f"R1 - {nom_test}"):
            risque, _ = modele_lgbm(train, test, FEATURES_R1)
            r = mesurer(test["en_retard"], risque, seuil)
            mlflow.log_params(PARAMS)
            mlflow.log_param("modele", "R1")
            mlflow.log_param("test", nom_test)
            mlflow.log_param("features", ",".join(FEATURES_R1))
            mlflow.log_metrics(r)
        afficher("R1", nom_test, r)