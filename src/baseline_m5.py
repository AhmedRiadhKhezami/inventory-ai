from pathlib import Path

import pandas as pd

from src.metrics import wape

RACINE = Path(__file__).resolve().parent.parent
CHEMIN = RACINE / "data" / "processed" / "sales_ca1_clean.parquet"
TESTS = {"Test 1": "2016-02-29", "Test 2": "2016-03-28", "Test final": "2016-04-25"}


def baseline_moy28(df, debut):
    """WAPE de la règle : ventes des 28 prochains jours = moyenne des 28 derniers x 28."""
    debut = pd.Timestamp(debut)
    passe = df[(df["date"] >= debut - pd.Timedelta(days=28)) & (df["date"] < debut)]
    futur = df[(df["date"] >= debut) & (df["date"] < debut + pd.Timedelta(days=28))]

    prevu = passe.groupby("id")["sales"].mean() * 28
    vrai = futur.groupby("id")["sales"].sum()

    t = pd.concat([vrai.rename("vrai"), prevu.rename("prevu")], axis=1)
    t = t.dropna(subset=["vrai"]).fillna(0)
    return wape(t["vrai"], t["prevu"])


if __name__ == "__main__":
    df = pd.read_parquet(CHEMIN)
    for nom, debut in TESTS.items():
        print(f"{nom:10s} | début {debut} | WAPE moyenne 28 jours : "
              f"{baseline_moy28(df, debut) * 100:.1f} %")