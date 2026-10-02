from pathlib import Path

import lightgbm as lgb
import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, precision_score, recall_score

RACINE = Path(__file__).resolve().parent.parent
CHEMIN = RACINE / "data" / "processed" / "usaid_clean.parquet"
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
HISTORIQUE = [
    "hist_retard_global", "hist_retard_pays", "hist_retard_fournisseur",
    "hist_retard_mode", "hist_nb_envois_pays",
]
FEATURES_R1 = CATEGORIES + NUMERIQUES
FEATURES_R1B = FEATURES_R1 + HISTORIQUE

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
    return df.reset_index(drop=True)


def ajouter_historique(df, jours_avant=30, fenetre=180):
    """Pour chaque envoi : % de retard récent, calculé SEULEMENT avec les envois
    déjà livrés à la date de décision (= date prévue - jours_avant)."""
    df = df.copy()
    decision = (df["date_prevue"] - pd.Timedelta(days=jours_avant)).to_numpy()
    reel = df["date_reelle"].to_numpy()
    retard = df["en_retard"].to_numpy()
    pays = df["Country"].astype(str).to_numpy()
    fournisseur = df["Vendor"].astype(str).to_numpy()
    mode = df["Fulfill Via"].astype(str).to_numpy()
    duree = np.timedelta64(fenetre, "D")

    def taux(masque):
        return retard[masque].mean() if masque.any() else np.nan

    g, p, v, m, charge = [], [], [], [], []
    for i in range(len(df)):
        connu = (reel < decision[i]) & (reel >= decision[i] - duree)
        meme_pays = connu & (pays == pays[i])
        g.append(taux(connu))
        p.append(taux(meme_pays))
        v.append(taux(connu & (fournisseur == fournisseur[i])))
        m.append(taux(connu & (mode == mode[i])))
        charge.append(meme_pays.sum())

    df["hist_retard_global"] = g
    df["hist_retard_pays"] = p
    df["hist_retard_fournisseur"] = v
    df["hist_retard_mode"] = m
    df["hist_nb_envois_pays"] = charge
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


def auc_par_mode(test, risque):
    """AUC séparée pour les envois usine (Direct Drop) et entrepôt (From RDC)."""
    t = test.assign(risque=risque)
    return {f"auc_{str(mode).split()[-1]}": roc_auc_score(g["en_retard"], g["risque"])
            for mode, g in t.groupby("Fulfill Via", observed=True)}


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
          f"| AUC usine : {r['auc_Drop']:.3f} | AUC entrepôt : {r['auc_RDC']:.3f} "
          f"| Rappel : {r['rappel']*100:.1f} % | Précision : {r['precision']*100:.1f} %")


if __name__ == "__main__":
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("retard-import")

    df = ajouter_historique(charger())

    for nom_test, annee in TESTS.items():
        train = df[df["annee"] < annee]
        test = df[df["annee"] == annee]
        seuil = train["en_retard"].mean()

        risque = baseline(train, test)
        r = mesurer(test["en_retard"], risque, seuil) | auc_par_mode(test, risque)
        afficher("Baseline", nom_test, r)

        for nom_modele, features in [("R1", FEATURES_R1), ("R1B", FEATURES_R1B)]:
            with mlflow.start_run(run_name=f"{nom_modele} - {nom_test}"):
                risque, _ = modele_lgbm(train, test, features)
                r = mesurer(test["en_retard"], risque, seuil) | auc_par_mode(test, risque)
                mlflow.log_params(PARAMS)
                mlflow.log_param("modele", nom_modele)
                mlflow.log_param("test", nom_test)
                mlflow.log_param("features", ",".join(features))
                mlflow.log_metrics(r)
            afficher(nom_modele, nom_test, r)