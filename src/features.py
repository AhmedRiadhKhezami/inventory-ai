import pandas as pd

FEATURES_C = [
    "moy_7j", "moy_28j", "moy_56j", "part_jours_vente", "moy_meme_jour",
    "horizon", "sell_price", "jour_semaine", "mois", "evenement", "snap_CA",
    "prix_relatif", "tendance", "jours_sans_vente", "dept_id", "cat_id",
]

ECONOMIE = [
    "petrole", "essence", "dollar", "confiance",
    "petrole_var_30j", "essence_var_30j", "inflation_12m",
]

GEOPOLITIQUE = ["gpr", "gpr_usa", "gpr_jour", "gpr_7j", "gpr_30j", "gscpi"]

FEATURES_D = FEATURES_C + ECONOMIE
FEATURES_E = FEATURES_D + GEOPOLITIQUE

FEATURES = FEATURES_C  # nom gardé pour les anciens fichiers


def charger_donnees(chemin):
    """Charge le tableau propre et ajoute les colonnes de calendrier."""
    df = pd.read_parquet(chemin)
    df = df.sort_values(["item_id", "date"]).reset_index(drop=True)
    df["jour_semaine"] = df["date"].dt.dayofweek
    df["mois"] = df["date"].dt.month
    df["evenement"] = df["event_name_1"].notna().astype(int)
    return df


def construire_exercice(df, origine, signaux=None):
    """Un "lundi matin" : indices calculés jusqu'à la veille,
    et les 28 jours suivants à prévoir."""
    origine = pd.Timestamp(origine)

    # Ventes connues : les 56 jours AVANT l'origine
    hist = df[(df["date"] < origine) & (df["date"] >= origine - pd.Timedelta(days=56))]

    f = hist.groupby("item_id")["sales"].mean().rename("moy_56j").to_frame()
    f["moy_28j"] = hist[hist["date"] >= origine - pd.Timedelta(days=28)].groupby("item_id")["sales"].mean()
    f["moy_7j"] = hist[hist["date"] >= origine - pd.Timedelta(days=7)].groupby("item_id")["sales"].mean()
    f["part_jours_vente"] = (hist["sales"] > 0).groupby(hist["item_id"]).mean()
    f["prix_moy_56j"] = hist.groupby("item_id")["sell_price"].mean()
    f["derniere_vente"] = hist[hist["sales"] > 0].groupby("item_id")["date"].max()

    moy_jour = (hist.groupby(["item_id", "jour_semaine"])["sales"].mean()
                    .rename("moy_meme_jour").reset_index())

    # Les 28 jours à prévoir
    cible = df[(df["date"] >= origine) & (df["date"] < origine + pd.Timedelta(days=28))]
    cible = cible[["item_id", "dept_id", "cat_id", "date", "sales", "sell_price",
                   "jour_semaine", "mois", "evenement", "snap_CA"]].copy()

    cible = cible.merge(f.reset_index(), on="item_id", how="left")
    cible = cible.merge(moy_jour, on=["item_id", "jour_semaine"], how="left")

    # Indices calculés
    cible["horizon"] = (cible["date"] - origine).dt.days + 1
    cible["prix_relatif"] = cible["sell_price"] / cible["prix_moy_56j"]
    cible["tendance"] = cible["moy_7j"] / (cible["moy_28j"] + 0.1)
    cible["jours_sans_vente"] = (origine - cible["derniere_vente"]).dt.days

    # Rayon et catégorie = des groupes, pas des nombres
    cible["dept_id"] = pd.Categorical(cible["dept_id"], categories=sorted(df["dept_id"].unique()))
    cible["cat_id"] = pd.Categorical(cible["cat_id"], categories=sorted(df["cat_id"].unique()))

    # Signaux externes : ceux CONNUS le lundi matin, les mêmes pour les 28 jours
    if signaux is not None:
        ligne = signaux[signaux["date"] == origine].drop(columns="date")
        for col in ligne.columns:
            cible[col] = ligne[col].iloc[0]

    return cible


def construire_entrainement(df, debut_test, nb_origines=50, signaux=None):
    """Fabrique plusieurs "lundis matin" dans le passé, AVANT le test."""
    debut_test = pd.Timestamp(debut_test)
    origines = pd.date_range(end=debut_test - pd.Timedelta(days=28),
                             periods=nb_origines, freq="14D")
    return pd.concat([construire_exercice(df, o, signaux) for o in origines],
                     ignore_index=True)