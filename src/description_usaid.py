from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

RACINE = Path(__file__).resolve().parent.parent
CHEMIN = RACINE / "data" / "processed" / "usaid_clean.parquet"
CHEMIN_GSCPI = RACINE / "data" / "raw" / "external" / "gscpi.csv"
GROUPE = ["Fulfill Via", "Shipment Mode", "region_origine"]


def charger():
    """Lignes de 2010 à 2015, comme dans les modèles."""
    df = pd.read_parquet(CHEMIN)
    df = df[df["date_prevue"] >= "2010-01-01"].copy()
    df["annee"] = df["date_prevue"].dt.year
    df["region_origine"] = df["region_origine"].fillna("Inconnue")
    return df


def taux_par_facteur(df):
    """Part des lignes en retard, au total et par facteur."""
    print(f"Lignes : {len(df)} | en retard : {df['en_retard'].mean() * 100:.1f} %")
    tard = df.loc[df["en_retard"] == 1, "retard_jours"]
    print(f"Retard quand en retard : moyenne {tard.mean():.1f} j | médiane {tard.median():.0f} j\n")
    for col in GROUPE:
        t = df.groupby(col, observed=True)["en_retard"].agg(["size", "mean"])
        t["part_lignes_%"] = (t["size"] / len(df) * 100).round(1)
        t["retard_%"] = (t["mean"] * 100).round(1)
        print(t[["size", "part_lignes_%", "retard_%"]], "\n")


def correlation_gscpi(df):
    """Taux de retard de chaque mois comparé au GSCPI du même mois."""
    g = pd.read_csv(CHEMIN_GSCPI, parse_dates=["date"])
    g["mois"] = g["date"].dt.to_period("M")
    m = (df.assign(mois=df["date_prevue"].dt.to_period("M"))
           .groupby("mois")["en_retard"].mean().rename("retard").reset_index()
           .merge(g[["mois", "gscpi"]], on="mois"))
    print(f"Corrélation retard mensuel / GSCPI : {m['retard'].corr(m['gscpi']):.2f} ({len(m)} mois)\n")


def marges(df):
    """Marge P90 globale (règle simple) contre marge P90 par route."""
    for annee in (2013, 2014, 2015):
        train = df[df["annee"] < annee]
        test = df[df["annee"] == annee]
        globale = train["retard_jours"].quantile(0.9)
        par_route = (train.groupby(GROUPE, observed=True)["retard_jours"].quantile(0.9)
                          .rename("marge").reset_index())
        m = test.merge(par_route, on=GROUPE, how="left")["marge"].fillna(globale).to_numpy()
        y = test["retard_jours"].to_numpy()
        print(f"{annee} | P90 global : {globale:.0f} j, couverture {(y <= globale).mean() * 100:.1f} % "
              f"| P90 par route : marge moyenne {m.mean():.1f} j, couverture {(y <= m).mean() * 100:.1f} %")
    print()


def envois_entrepot(df):
    """Combien d'envois différents derrière les lignes entrepôt des tests 1 et 2."""
    t = df[(df["Fulfill Via"] == "From RDC") & df["annee"].isin([2013, 2014])]
    melange = t.groupby("ASN/DN #")["en_retard"].nunique().gt(1).sum()
    print(f"Entrepôt, tests 1-2 : {len(t)} lignes, {t['ASN/DN #'].nunique()} envois, "
          f"{melange} envois avec des résultats différents entre leurs lignes")


def oracle_entrepot(df):
    """Test impossible en vrai : on donne le VRAI taux de retard des AUTRES envois
    entrepôt du même mois (et du même pays). Sert à voir la limite des données."""
    r = df[df["Fulfill Via"] == "From RDC"].copy()
    r["mois"] = r["date_prevue"].dt.to_period("M")
    t = r[r["annee"].isin([2013, 2014])]
    for nom, cles in [("même mois", ["mois"]), ("même mois + même pays", ["mois", "Country"])]:
        valeurs = []
        for _, ligne in t.iterrows():
            masque = r["ASN/DN #"] != ligne["ASN/DN #"]
            for c in cles:
                masque &= r[c] == ligne[c]
            valeurs.append(r.loc[masque, "en_retard"].mean() if masque.any() else np.nan)
        v = np.array(valeurs)
        ok = ~np.isnan(v)
        print(f"Oracle {nom} : AUC {roc_auc_score(t['en_retard'][ok], v[ok]):.3f} ({ok.sum()} lignes)")


if __name__ == "__main__":
    df = charger()
    taux_par_facteur(df)
    correlation_gscpi(df)
    marges(df)
    envois_entrepot(df)
    oracle_entrepot(df)