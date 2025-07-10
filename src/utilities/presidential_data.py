import os
import re

import pandas as pd

POLAND_RAW_DATA = os.path.join(os.getcwd(), "data", "raw", "poland")

BASE_COLUMNS_MAP = {
    # 2025
    "Nr komisji": "polling_station_id",
    "Teryt Gminy": "teryt_gmina",
    # "Teryt Powiatu": "teryt_powiat",
    "Liczba wyborców uprawnionych do głosowania (umieszczonych w spisie, z uwzględnieniem dodatkowych formularzy) w chwili zakończenia głosowania": "eligible_voters",
    "Liczba kart wyjętych z urny": "ballots_cast",
    # round 2
    "Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów (z kart ważnych)": "valid_votes",
    # round 1
    "Liczba głosów ważnych oddanych łącznie na obu kandydatów (z kart ważnych)": "valid_votes",
    # 2020
    "Numer obwodu": "polling_station_id",
    "Kod TERYT": "teryt_gmina",
    "Liczba wyborców uprawnionych do głosowania": "eligible_voters",
    "Liczba kart wyjętych z urny": "ballots_cast",
    "Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów": "valid_votes",
    # 2015
    "Liczba głosów ważnych": "valid_votes",
}

CANDIDATE_SURNAMES_BY_YEAR = {
    "2015": [
        "braun",
        "duda",
        "jarubas",
        "komorowski",
        "korwin-mikke",
        "kowalski",
        "kukiz",
        "ogórek",
        "palikot",
        "tanajno",
        "wilk",
    ],
    "2020": [
        "biedroń",
        "bosak",
        "duda",
        "hołownia",
        "jakubiak",
        "kosiniak-kamysz",
        "piotrowski",
        "tanajno",
        "trzaskowski",
        "witkowski",
        "żółtek",
    ],
    "2025": [
        "bartoszewicz",
        "biejat",
        "braun",
        "hołownia",
        "jakubiak",
        "maciak",
        "mentzen",
        "nawrocki",
        "senyszyn",
        "stanowski",
        "trzaskowski",
        "woch",
        "zandberg",
    ],
}


def get_candidate_rename_map(df, year):
    surnames = CANDIDATE_SURNAMES_BY_YEAR.get(str(year), [])
    rename_map = {
        col: surname
        for col in df.columns
        for surname in surnames
        if surname in col.lower()
    }
    return rename_map


def extract_postal_code(address):
    match = re.search(r"\b\d{2}-\d{3}\b", str(address))
    return match.group(0) if match else None


def load_data(year, round, ext="csv"):
    file_path = os.path.join(
        POLAND_RAW_DATA, f"{year}_presidential", f"round{round}.{ext}"
    )
    if ext == "csv":
        df = pd.read_csv(file_path, sep=";", encoding="utf-8")
    elif ext == "xls":
        df = pd.read_excel(file_path, dtype={"TERYT gminy": str})
    else:
        raise NotImplementedError(f"Cannot load file with {ext} ext!")
    # Normalize column names: replace non-breaking spaces, strip whitespace
    df.columns = df.columns.str.replace("\xa0", " ", regex=False).str.strip()
    return df


def process_df(df, year, final_cols=[]):
    # Rename columns - to have same naming convention for all files
    df = df.rename(columns=BASE_COLUMNS_MAP)

    # Shorten candidate columns - risky if two candidates with the same surname

    candidate_rename_map = get_candidate_rename_map(df, year=year)
    df.rename(columns=candidate_rename_map, inplace=True)

    df = df.rename(columns=candidate_rename_map)
    # Assuming, if postal code column exits, no need for extraction
    if "postal_code" not in df.columns:
        # Get postal code from address ("siedziba")
        df["postal_code"] = df["Siedziba"].apply(extract_postal_code)
    final_cols = (
        list(set(BASE_COLUMNS_MAP.values()))  # ensure uniqueness only here
        + list(candidate_rename_map.values())  # may have overlaps, OK
        + ["postal_code"]
        + final_cols
    )
    df = df[final_cols]
    return df


def get_df(year, round, ext="csv"):
    df = load_data(year, round, ext)
    return process_df(df, year)


def join_both_rounds(cand_A, cand_B, df_r1, df_r2):
    """
    Cleans and merges two election DataFrames (round 1 and round 2).

    Parameters:
        cand_A (str): Column name of candidate A.
        cand_B (str): Column name of candidate B.
        df_r1 (pd.DataFrame): Round 1 DataFrame.
        df_r2 (pd.DataFrame): Round 2 DataFrame.

    Returns:
        pd.DataFrame: Merged DataFrame with candidate columns suffixed.
    """

    def clean_df(df):
        keep_columns = [
            "teryt_gmina",
            "polling_station_id",
            cand_A,
            cand_B,
            "postal_code",
        ]
        # Step 1: Keep only selected columns
        df = df[keep_columns]
        df = df.dropna(subset=["teryt_gmina"])
        # Step 2: Convert teryt_gmina to integer
        df["teryt_gmina"] = df["teryt_gmina"].astype(int)
        return df

    df_r1 = clean_df(df_r1)
    df_r2 = clean_df(df_r2)

    # Join both rounds

    df = pd.merge(
        df_r1,
        df_r2,
        on=["teryt_gmina", "polling_station_id", "postal_code"],
        how="inner",
        suffixes=("_r1", "_r2"),
    )
    return df
