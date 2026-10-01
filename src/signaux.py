import pandas as pd

DOSSIER = "data/raw/external"
SORTIE = "data/processed/signaux_externes.parquet"

# Fichier : nombre de jours avant que le chiffre soit connu
DELAIS = {
    "petrole.csv": 1,
    "essence.csv": 1,
    "dollar.csv": 1,
    "gpr_jour.csv": 1,
    "inflation.csv": 45,
    "confiance.csv": 31,
    "gpr_mois.csv": 31,
    "gscpi.csv": 38,
}


def lire(fichier):
    """Lit un CSV de signal. Les fichiers FRED ont une colonne 'valeur' :
    on la renomme avec le nom du signal (ex : 'petrole')."""
    t = pd.read_csv(f"{DOSSIER}/{fichier}", parse_dates=["date"])
    if "valeur" in t.columns:
        t = t.rename(columns={"valeur": fichier.replace(".csv", "")})
    return t


def construire_table_jour(debut="2009-01-01", fin="2016-12-31"):
    """1 ligne par jour. Chaque signal = la dernière valeur DÉJÀ CONNUE ce jour-là."""
    table = pd.DataFrame({"date": pd.date_range(debut, fin, freq="D")})

    for fichier, delai in DELAIS.items():
        s = lire(fichier).dropna()
        s["date_connue"] = s["date"] + pd.Timedelta(days=delai)
        s = s.drop(columns="date").sort_values("date_connue")
        table = pd.merge_asof(table, s, left_on="date", right_on="date_connue",
                              direction="backward").drop(columns="date_connue")

    # Variations : souvent plus utiles que le chiffre brut
    table["petrole_var_30j"] = table["petrole"] / table["petrole"].shift(30) - 1
    table["essence_var_30j"] = table["essence"] / table["essence"].shift(30) - 1
    table["inflation_12m"] = table["inflation"] / table["inflation"].shift(365) - 1
    return table


if __name__ == "__main__":
    table = construire_table_jour()
    table.to_parquet(SORTIE, index=False)

    print("Taille :", table.shape)
    print("\nCases vides par colonne (période M5) :")
    print(table[table["date"] >= "2011-01-29"].isna().sum())
    print("\nPremier jour de M5 :")
    print(table[table["date"] == "2011-01-29"].T)