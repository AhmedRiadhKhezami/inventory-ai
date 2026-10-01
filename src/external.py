import os
import pandas as pd

DOSSIER = "data/raw/external"

SERIES_FRED = {
    "DCOILWTICO": "petrole",
    "GASREGW": "essence",
    "CPIAUCSL": "inflation",
    "UMCSENT": "confiance",
    "DTWEXBGS": "dollar",
}


def telecharger_fred(code):
    """Télécharge une série de FRED. Renvoie un tableau : date, valeur."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}"
    serie = pd.read_csv(url)
    serie.columns = ["date", "valeur"]
    serie["date"] = pd.to_datetime(serie["date"])
    serie["valeur"] = pd.to_numeric(serie["valeur"], errors="coerce")
    return serie


def lire_gpr():
    """Lit les 2 fichiers GPR (téléchargés à la main). Renvoie : mensuel, journalier."""
    mois = pd.read_excel(f"{DOSSIER}/data_gpr_export.xls")
    mois = mois[["month", "GPR", "GPRC_USA"]].rename(
        columns={"month": "date", "GPR": "gpr", "GPRC_USA": "gpr_usa"})
    mois["date"] = pd.to_datetime(mois["date"])
    mois = mois.dropna(subset=["gpr"])

    jour = pd.read_excel(f"{DOSSIER}/data_gpr_daily_recent.xls")
    jour = jour[["date", "GPRD", "GPRD_MA7", "GPRD_MA30"]].rename(
        columns={"GPRD": "gpr_jour", "GPRD_MA7": "gpr_7j", "GPRD_MA30": "gpr_30j"})
    jour["date"] = pd.to_datetime(jour["date"])
    return mois, jour


def lire_gscpi():
    """Lit le fichier GSCPI (téléchargé à la main), onglet des chiffres."""
    g = pd.read_excel(f"{DOSSIER}/gscpi_data.xls",
                      sheet_name="GSCPI Monthly Data", usecols=[0, 1])
    g.columns = ["date", "gscpi"]
    g = g.dropna()
    g["date"] = pd.to_datetime(g["date"]).dt.to_period("M").dt.to_timestamp()
    return g


def resume(nom, tableau):
    print(f"{nom} : {len(tableau)} lignes, "
          f"du {tableau['date'].min().date()} au {tableau['date'].max().date()}")


if __name__ == "__main__":
    os.makedirs(DOSSIER, exist_ok=True)

    # 1. FRED : téléchargement automatique
    for code, nom in SERIES_FRED.items():
        serie = telecharger_fred(code)
        serie.to_csv(f"{DOSSIER}/{nom}.csv", index=False)
        resume(nom, serie)

    # 2. GPR et GSCPI : fichiers téléchargés à la main, remis au propre
    gpr_mois, gpr_jour = lire_gpr()
    gscpi = lire_gscpi()

    gpr_mois.to_csv(f"{DOSSIER}/gpr_mois.csv", index=False)
    gpr_jour.to_csv(f"{DOSSIER}/gpr_jour.csv", index=False)
    gscpi.to_csv(f"{DOSSIER}/gscpi.csv", index=False)

    resume("gpr_mois", gpr_mois)
    resume("gpr_jour", gpr_jour)
    resume("gscpi", gscpi)