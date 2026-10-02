import pandas as pd
from sklearn.metrics import roc_auc_score, precision_score, recall_score

CHEMIN = "data/processed/usaid_clean.parquet"
TESTS = {"Test 1": 2013, "Test 2": 2014}
GROUPE = ["Fulfill Via", "Shipment Mode", "region_origine"]


def charger():
    """Envois depuis 2010, avec l'année de livraison prévue."""
    df = pd.read_parquet(CHEMIN)
    df = df.dropna(subset=["date_prevue"])
    df = df[df["date_prevue"] >= "2010-01-01"].copy()
    df["annee"] = df["date_prevue"].dt.year
    df["region_origine"] = df["region_origine"].fillna("Inconnue")
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
    taux = train.groupby(GROUPE)["en_retard"].mean().rename("risque").reset_index()
    t = test.merge(taux, on=GROUPE, how="left")
    t["risque"] = t["risque"].fillna(train["en_retard"].mean())
    return t["risque"].to_numpy()


if __name__ == "__main__":
    df = charger()
    for nom, annee in TESTS.items():
        train = df[df["annee"] < annee]
        test = df[df["annee"] == annee]

        risque = baseline(train, test)
        seuil = train["en_retard"].mean()
        r = mesurer(test["en_retard"], risque, seuil)

        print(f"{nom} ({annee}) | retards réels : {test['en_retard'].mean()*100:.1f} % "
              f"| AUC : {r['auc']:.3f} | Rappel : {r['rappel']*100:.1f} % "
              f"| Précision : {r['precision']*100:.1f} % | Alertes : {r['pct_alertes']*100:.1f} %")
              