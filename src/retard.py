from pathlib import Path

import lightgbm as lgb
import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, precision_score, recall_score

RACINE = Path(__file__).resolve().parent.parent
CHEMIN = RACINE / "data" / "processed" / "usaid_clean.parquet"
CHEMIN_SIGNAUX = RACINE / "data" / "processed" / "signaux_externes.parquet"
TESTS = {"Test 1": 2013, "Test 2": 2014, "Test final": 2015}
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
EXTERNES = [
    "petrole", "essence", "dollar", "confiance",
    "petrole_var_30j", "essence_var_30j", "inflation_12m",
    "gpr", "gpr_usa", "gpr_jour", "gpr_7j", "gpr_30j", "gscpi",
]


def noms_historique(suffixe):
    return [f"hist_retard_global{suffixe}", f"hist_retard_pays{suffixe}",
            f"hist_retard_fournisseur{suffixe}", f"hist_retard_mode{suffixe}",
            f"hist_nb_envois_pays{suffixe}"]


FEATURES_R1 = CATEGORIES + NUMERIQUES
FEATURES_R2 = FEATURES_R1 + noms_historique("_60") + noms_historique("_180")
FEATURES_R3 = FEATURES_R2 + EXTERNES

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


def ajouter_historique(df, fenetre, suffixe, jours_avant=30):
    """Pour chaque envoi : % de retard récent, calculé SEULEMENT avec les envois
    déjà livrés à la date de décision (= date prévue - jours_avant),
    SANS les lignes du même envoi (elles partagent presque toujours le résultat).
    S'il n'y a pas de numéro d'envoi, chaque ligne est son propre envoi."""
    df = df.copy()
    decision = (df["date_prevue"] - pd.Timedelta(days=jours_avant)).to_numpy()
    reel = df["date_reelle"].to_numpy()
    retard = df["en_retard"].to_numpy()
    pays = df["Country"].astype(str).to_numpy()
    fournisseur = df["Vendor"].astype(str).to_numpy()
    mode = df["Fulfill Via"].astype(str).to_numpy()
    if "ASN/DN #" in df.columns:
        envoi = df["ASN/DN #"].astype(str).to_numpy()
    else:
        envoi = np.arange(len(df)).astype(str)
    duree = np.timedelta64(fenetre, "D")

    def taux(masque):
        return retard[masque].mean() if masque.any() else np.nan

    g, p, v, m, charge = [], [], [], [], []
    for i in range(len(df)):
        connu = ((reel < decision[i]) & (reel >= decision[i] - duree)
                 & (envoi != envoi[i]))
        meme_pays = connu & (pays == pays[i])
        g.append(taux(connu))
        p.append(taux(meme_pays))
        v.append(taux(connu & (fournisseur == fournisseur[i])))
        m.append(taux(connu & (mode == mode[i])))
        charge.append(meme_pays.sum())

    for nom, valeurs in zip(noms_historique(suffixe), [g, p, v, m, charge]):
        df[nom] = valeurs
    return df


def ajouter_signaux(df, jours_avant=30):
    """Indicateurs externes connus à la date de décision (= date prévue - jours_avant).
    La table des signaux respecte déjà les délais de publication."""
    signaux = pd.read_parquet(CHEMIN_SIGNAUX)[["date"] + EXTERNES]
    df = df.copy()
    df["date_decision"] = df["date_prevue"] - pd.Timedelta(days=jours_avant)
    return df.merge(signaux.rename(columns={"date": "date_decision"}),
                    on="date_decision", how="left")


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