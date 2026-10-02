import pandas as pd
from ftfy import fix_text

CHEMIN_BRUT = "data/raw/usaid/Raw_Data.csv"
CHEMIN_PROPRE = "data/processed/usaid_clean.parquet"

USINE_PAYS = {
    "Aurobindo Unit III, India": "Inde",
    "Mylan (formerly Matrix) Nashik": "Inde",
    "Hetero Unit III Hyderabad IN": "Inde",
    "Cipla, Goa, India": "Inde",
    "Strides, Bangalore, India.": "Inde",
    "Alere Medical Co., Ltd.": "Japon",
    "Trinity Biotech, Plc": "Irlande",
    "ABBVIE Ludwigshafen Germany": "Allemagne",
    "Inverness Japan": "Japon",
    "ABBVIE (Abbott) Logis. UK": "Royaume-Uni",
    "BMS Meymac, France": "France",
    "Aspen-OSD, Port Elizabeth, SA": "Afrique du Sud",
    "Chembio Diagnostics Sys. Inc.": "États-Unis",
    "MSD, Haarlem, NL": "Pays-Bas",
    "Standard Diagnostics, Korea": "Corée du Sud",
    "Aurobindo Unit VII, IN": "Inde",
    "KHB Test Kit Facility, Shanghai China": "Chine",
    "Emcure Plot No.P-2, I.T-B.T. Park, Phase II, MIDC, Hinjwadi, Pune, India": "Inde",
    "GSK Mississauga (Canada)": "Canada",
    "Janssen-Cilag, Latina, IT": "Italie",
    "Micro labs, Verna, Goa, India": "Inde",
    "Cipla, Kurkumbh, India": "Inde",
    "Roche Basel": "Suisse",
    "Hetero, Jadcherla, unit 5, IN": "Inde",
    "Pacific Biotech, Thailand": "Thaïlande",
    "Cipla, Patalganga, India": "Inde",
    "Ranbaxy, Paonta Shahib, India": "Inde",
    "Bio-Rad Laboratories": "France",  # à vérifier
    "GSK Ware (UK)": "Royaume-Uni",
    "ABBVIE GmbH & Co.KG Wiesbaden": "Allemagne",
    "Gilead(Nycomed) Oranienburg DE": "Allemagne",
    "ABBVIE (Abbott) France": "France",
    "Bristol-Myers Squibb Anagni IT": "Italie",
    "Mylan,  H-12 & H-13, India": "Inde",
    "MSD Midrand, J'burg, SA": "Afrique du Sud",
    "GSK Cape Town Factory (South Africa)": "Afrique du Sud",
    "Roche Madrid": "Espagne",
    "Cipla Ltd A-42 MIDC Mahar. IN": "Inde",
    "BMS Evansville, US": "États-Unis",
    "Premier Med. Corp Ltd. India": "Inde",
    "GSK Aranda": "Espagne",
    "Boehringer Ing., Koropi, GR": "Grèce",
    "Orasure Technologies, Inc USA": "États-Unis",
    "BI, Ingelheim, Germany": "Allemagne",
    "MSD Elkton USA": "États-Unis",
    "Ranbaxy per Shasun Pharma": "Inde",
    "Inverness USA": "États-Unis",
    "MSD Manati, Puerto Rico, (USA)": "États-Unis",
    "Novartis Pharma Suffern, USA": "États-Unis",
    "Micro Labs, Hosur, India": "Inde",
    "Macleods Daman Plant INDIA": "Inde",
    "ABBVIE (Abbott) St. P'burg USA": "États-Unis",
    "GSK Crawley": "Royaume-Uni",
    "Orasure Technologies, Inc": "États-Unis",
    "Boehringer Ingelheim Roxane US": "États-Unis",
    "Novartis Pharma AG, Switzerland": "Suisse",
    "bioLytical Laboratories": "Canada",
    "Ipca Dadra/Nagar Haveli IN": "Inde",
    "Micro Labs Ltd. (Brown & Burk), India": "Inde",
    "MSD Patheon, Canada": "Canada",
    "GSK, U1, Poznan, Poland": "Pologne",
    "Human Diagnostic": "Allemagne",  # à vérifier
    "Ranbaxy Fine Chemicals LTD": "Inde",
    "MSD South Granville Australia": "Australie",
    "EY Laboratories, USA": "États-Unis",
    "Medopharm Malur Factory, INDIA": "Inde",
    "ABBVIE (Abbott) Japan Co. Ltd.": "Japon",
    "Janssen Ortho LLC, Puerto Rico": "États-Unis",
    "Guilin OSD site, No 17, China": "Chine",
    "Ranbaxy per Shasun Pharma Ltd": "Inde",
    "Gland Pharma Ltd Pally Factory": "Inde",
    "OMEGA Diagnostics, UK": "Royaume-Uni",
    "INVERNESS ORGENICS LINE": "Israël",  # à vérifier
    "Meditab (for Cipla) Daman IN": "Inde",
    "Weifa A.S., Hausmanngt. 6, P.O. Box 9113 Grønland, 0133, Oslo, Norway": "Norvège",
    "Premier Medical Corporation": "Inde",  # à vérifier
    "ABBVIE Labs North Chicago US": "États-Unis",
    "Medochemie Factory A, CY": "Chypre",
    "Remedica, Limassol, Cyprus": "Chypre",
    "GSK Barnard Castle UK": "Royaume-Uni",
    "Gland Pharma, Hyderabad, IN": "Inde",
    "Access BIO, L.C.": "États-Unis",  # à vérifier
    "Mepro Pharm Wadhwan Unit II": "Inde",
    "MedMira Inc.": "Canada",
    # Inconnus : "Not Applicable", "INVERNESS ANY", "ABBSP",
    # "BUNDI INTERNATIONAL DIAGNOSTICS LTD" → pas de pays
}

PAYS_REGION = {
    "Inde": "Asie", "Chine": "Asie", "Japon": "Asie", "Corée du Sud": "Asie",
    "Thaïlande": "Asie", "Israël": "Asie",
    "Allemagne": "Europe", "France": "Europe", "Royaume-Uni": "Europe",
    "Irlande": "Europe", "Pays-Bas": "Europe", "Italie": "Europe",
    "Suisse": "Europe", "Espagne": "Europe", "Grèce": "Europe",
    "Pologne": "Europe", "Norvège": "Europe", "Chypre": "Europe",
    "États-Unis": "Amérique", "Canada": "Amérique",
    "Afrique du Sud": "Afrique",
    "Australie": "Océanie",
}


def lire_date(colonne):
    """Transforme '14-Nov-06' en vraie date. Les textes non-dates deviennent vides."""
    return pd.to_datetime(colonne, format="%d-%b-%y", errors="coerce")


def nettoyer_usaid():
    df = pd.read_csv(CHEMIN_BRUT)
    df = df.rename(columns={df.columns[0]: "ID"})

    # 1. Réparer le texte abîmé (ex : "CÃ´te" → "Côte")
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(lambda x: fix_text(x) if isinstance(x, str) else x)

    # 2. Pays et région d'origine
    df["pays_origine"] = df["Manufacturing Site"].map(USINE_PAYS)
    df["region_origine"] = df["pays_origine"].map(PAYS_REGION)

    # 3. Dates et délais
    df["date_commande"] = lire_date(df["PO Sent to Vendor Date"])
    df["date_prevue"] = lire_date(df["Scheduled Delivery Date"])
    df["date_reelle"] = lire_date(df["Delivered to Client Date"])
    df["retard_jours"] = (df["date_reelle"] - df["date_prevue"]).dt.days
    df["en_retard"] = (df["retard_jours"] > 0).astype(int)
    df["delai_total_jours"] = (df["date_reelle"] - df["date_commande"]).dt.days

    # 4. Transport inconnu
    df["Shipment Mode"] = df["Shipment Mode"].fillna("Inconnu")
    return df


if __name__ == "__main__":
    df = nettoyer_usaid()
    df.to_parquet(CHEMIN_PROPRE, index=False)

    print("Envois :", len(df))
    print("Sans pays d'origine :", df["pays_origine"].isna().sum())
    print("\nPar région d'origine :")
    print(df["region_origine"].value_counts(dropna=False))
    print("\n% en retard par région d'origine :")
    print((df.groupby("region_origine")["en_retard"].mean() * 100).round(1))
    print("\n% en retard par transport :")
    print((df.groupby("Shipment Mode")["en_retard"].mean() * 100).round(1))