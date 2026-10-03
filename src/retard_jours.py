from src.retard import charger, GROUPE, TESTS


def retard_securite(train, test, quantile=0.9):
    """Marge de retard (en jours) à prévoir pour chaque envoi du test.
    = le retard que 9 envois sur 10 n'ont pas dépassé dans le passé,
    pour le même type d'envoi (usine/entrepôt + transport + région)."""
    global_q = train["retard_jours"].quantile(quantile)
    par_groupe = (train.groupby(GROUPE, observed=True)["retard_jours"]
                       .quantile(quantile).rename("marge").reset_index())
    t = test.merge(par_groupe, on=GROUPE, how="left")
    return t["marge"].fillna(global_q).to_numpy()


if __name__ == "__main__":
    df = charger()
    for nom, annee in TESTS.items():
        train = df[df["annee"] < annee]
        test = df[df["annee"] == annee]
        marge = retard_securite(train, test)
        couvert = (test["retard_jours"].to_numpy() <= marge).mean()
        print(f"{nom} ({annee}) | marge moyenne : {marge.mean():.1f} jours "
              f"| envois couverts : {couvert*100:.1f} %")

    print("\nMarge par type d'envoi (les 10 plus grandes) :")
    print(df.groupby(GROUPE, observed=True)["retard_jours"].quantile(0.9)
            .round(0).sort_values(ascending=False).head(10))