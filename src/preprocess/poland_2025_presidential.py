from src.utilities import get_data_path
import pandas as pd
import re
import os

# Base columns for geolocation and identification
base_cols = ["Teryt Gminy", "Teryt Powiatu", "postal_code"]


# Rename long anomaly-related column names to clean English
def get_rename_map(round: str):
    base_map = {
        "Nr komisji": "polling_station_id",
        "Teryt Gminy": "teryt_gmina",
        "Teryt Powiatu": "teryt_powiat",
        "Liczba wyborców uprawnionych do głosowania (umieszczonych w spisie, z uwzględnieniem dodatkowych formularzy) w chwili zakończenia głosowania": "eligible_voters",
        "Liczba kart wyjętych z urny": "ballots_cast",
    }

    # Add correct column for valid_votes based on round
    if round == "round1":
        valid_votes_col = "Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów (z kart ważnych)"
    elif round == "round2":
        valid_votes_col = (
            "Liczba głosów ważnych oddanych łącznie na obu kandydatów (z kart ważnych)"
        )
    else:
        raise RuntimeError(f"Cannot handle such round: {round}")

    base_map[valid_votes_col] = "valid_votes"
    return base_map


def extract_postal_code(address):
    match = re.search(r"\b\d{2}-\d{3}\b", str(address))
    return match.group(0) if match else None


def get_output_filename(file_name: str) -> str:
    base, ext = os.path.splitext(file_name)
    return f"{base}_clean.csv"


def save_processed(df, file_name: str):
    output_file = get_output_filename(file_name)
    output_path = get_data_path("processed", "poland", output_file)
    df.to_csv(output_path, index=False, sep=";", encoding="utf-8")
    print(f"✅ Saved cleaned data to: {output_path}")


def load_df(file_name: str):
    file_path = get_data_path("raw", "poland", file_name)
    df = pd.read_csv(file_path, sep=";", encoding="utf-8")
    # Normalize column names: replace non-breaking spaces, strip whitespace
    df.columns = df.columns.str.replace("\xa0", " ", regex=False).str.strip()
    return df


def process_df(file_name: str, round: str = None):
    print(f"📥 Loading {file_name} (round={round})...")
    df = load_df(file_name)
    df["postal_code"] = df["Siedziba"].apply(extract_postal_code)

    # Print and save missing postal codes
    missing_postal = df[df["postal_code"].isna()]
    if not missing_postal.empty:
        print("📭 Missing postal codes in 'Siedziba':")
        print(missing_postal["Siedziba"].to_string(index=False))

        # Select relevant columns for export
        # export_cols = ["Siedziba", "Typ obwodu"]
        # export_df = missing_postal[export_cols]

        # # Define path and save
        # export_path = get_data_path("processed", "poland", "missing_postal_codes.csv")
        # export_df.to_csv(export_path, index=False, sep=";", encoding="utf-8")
        # print(f"💾 Saved missing postal codes to: {export_path}")

        print("📌 Distinct 'Typ obwodu' values:")
        print(missing_postal["Typ obwodu"].dropna().unique())

        raise RuntimeError(
            f"Found {len(missing_postal)} entries without postal codes. Please check."
        )

    # Rename known columns
    rename_map = get_rename_map(round)
    df = df.rename(columns=rename_map)

    # Rename candidate columns to last names
    candidate_cols = [
        col for col in df.columns if re.match(r"^[A-ZĄĆĘŁŃÓŚŹŻ\-]+\s", col)
    ]
    candidate_rename_map = {col: col.split()[0].capitalize() for col in candidate_cols}
    df = df.rename(columns=candidate_rename_map)

    final_cols = (
        ["polling_station_id", "teryt_gmina", "teryt_powiat", "postal_code"]
        + list(rename_map.values())[3:]
        + list(candidate_rename_map.values())
    )
    df = df[final_cols]

    # Nullable IDs
    nullable_ints = ["teryt_gmina", "teryt_powiat"]

    # Convert nullable IDs to Int64
    for col in nullable_ints:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(pd.Int64Dtype())

    # Convert all others to regular int (postal_code stays str)
    numeric_cols = [
        col for col in df.columns if col not in nullable_ints + ["postal_code"]
    ]
    df[numeric_cols] = (
        df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
    )

    return df
