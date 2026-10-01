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


if __name__ == "__main__":
    os.makedirs(DOSSIER, exist_ok=True)
    for code, nom in SERIES_FRED.items():
        serie = telecharger_fred(code)
        serie.to_csv(f"{DOSSIER}/{nom}.csv", index=False)
        print(f"{nom} : {len(serie)} lignes, "
              f"du {serie['date'].min().date()} au {serie['date'].max().date()}")