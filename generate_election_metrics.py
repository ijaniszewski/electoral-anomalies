import pandas as pd
from src.utilities import get_data_path

# Use the same file name as earlier
file_name = "2025_presidential_round2.csv"
cleaned_path = get_data_path("processed", "poland", f"{file_name[:-4]}_clean.csv")

# Load the cleaned DataFrame
df = pd.read_csv(cleaned_path, sep=";", encoding="utf-8")

print("✅ Cleaned DataFrame loaded.")
# print(df.head())

## TOTALS ###
total_voters = df["ballots_cast"].sum()
total_eligible = df["eligible_voters"].sum()
overall_turnout = total_voters / total_eligible if total_eligible > 0 else None

# Sum votes for candidates
nawrocki_votes = df["Nawrocki"].sum()
trzaskowski_votes = df["Trzaskowski"].sum()

print("🧮 Total Summary")
print(f"✔️  Eligible voters: {total_eligible}")
print(f"🗳️  Voters who cast ballots: {total_voters}")
print(f"📊 Overall turnout: {overall_turnout:.4f}")
print("\n🧾 Vote totals:")
print(f"🟦 Nawrocki:     {nawrocki_votes}")
print(f"🟥 Trzaskowski:  {trzaskowski_votes}")

# df["postal_code"] = df["postal_code"].str.replace("-", "", regex=False)
# Remove rows where teryt_powiat is null (i.e. NaN)
df = df[df["postal_code"].notna()]

# Count remaining rows
record_count = len(df)

print(f"✅ Remaining records after filtering: {record_count}")

# from src.analysis.cluster_stations_by_postcode import cluster_polling_stations


# df = pd.read_csv(
#     get_data_path("processed", "poland", "2025_presidential_round2_clean.csv"), sep=";"
# )
# clustered_df, leftovers = cluster_polling_stations(df)

# num_clusters = clustered_df["cluster_id"].nunique()
# print(f"🧮 Total unique clusters: {num_clusters}")

# Save clustered version if needed
# clustered_df.to_csv(
#     get_data_path("processed", "poland", "2025_presidential_round2_clustered.csv"),
#     index=False,
#     sep=";",
# )
