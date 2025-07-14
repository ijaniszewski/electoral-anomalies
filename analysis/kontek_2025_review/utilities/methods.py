import pandas as pd

from scipy.stats import median_abs_deviation


def check_k_thresholds(df, cand_A, cand_B, score_suffix, k_values=[2.0, 2.5, 3.0]):
    """
    Checks how many times each candidate's score exceeds specified k thresholds.

    Parameters:
        df (pd.DataFrame): The DataFrame containing the candidate scores.
        cand_A (str): Name of candidate A (column prefix).
        cand_B (str): Name of candidate B (column prefix).
        score_suffix (str): Suffix used for the score column.
        k_values (list or iterable): List of threshold values to check.

    Returns:
        None. Prints results to stdout.
    """
    for k in k_values:
        count_A = (df[f"{cand_A}{score_suffix}"] > k).sum()
        count_B = (df[f"{cand_B}{score_suffix}"] > k).sum()
        print(f"k > {k}")
        print(f"{cand_A}: {count_A}")
        print(f"{cand_B}: {count_B}")
        print("---")


def mad(series):
    """Median Absolute Deviation"""
    return median_abs_deviation(series)


def add_anomaly_1(df, cand_A, cand_B, new_col_name="k_score_1"):
    # mediana w grupie
    df[cand_A + "_median_r2"] = df.groupby("bucket")[cand_A + "_r2"].transform("median")
    df[cand_B + "_median_r2"] = df.groupby("bucket")[cand_B + "_r2"].transform("median")

    # MAD w grupie
    df[cand_A + "_MAD_r2"] = df.groupby("bucket")[cand_A + "_r2"].transform(mad)
    df[cand_B + "_MAD_r2"] = df.groupby("bucket")[cand_B + "_r2"].transform(mad)

    df[cand_A + f"_{new_col_name}"] = (
        df[cand_A + "_r2"] - df[cand_A + "_median_r2"]
    ) / df[cand_A + "_MAD_r2"]
    df[cand_B + f"_{new_col_name}"] = (
        df[cand_B + "_r2"] - df[cand_B + "_median_r2"]
    ) / df[cand_B + "_MAD_r2"]

    df = df.drop(
        columns=[
            f"{cand_A}_median_r2",
            f"{cand_B}_median_r2",
            f"{cand_A}_MAD_r2",
            f"{cand_B}_MAD_r2",
        ]
    )

    return df


def add_anomaly_2(df, cand_A, cand_B, new_col_name="k_score_2"):
    # wzgledny wzrost między pierwszą a drugą turą
    df[cand_A + "_increase"] = df[cand_A + "_r2"] / df[cand_A + "_r1"]
    df[cand_B + "_increase"] = df[cand_B + "_r2"] / df[cand_B + "_r1"]

    # roznica wzglednego wzrostu miedzy kandydatami
    # wzrost A w porównaniu do B
    df["relative_increase_diff_" + cand_A] = (
        df[cand_A + "_increase"] - df[cand_B + "_increase"]
    )
    # wzrost B w porównaniu do A
    df["relative_increase_diff_" + cand_B] = (
        df[cand_B + "_increase"] - df[cand_A + "_increase"]
    )

    # mediana i mad różnicy względnego wzrostu poparcia
    df["relative_increase_diff_" + cand_A + "_median"] = df.groupby("bucket")[
        "relative_increase_diff_" + cand_A
    ].transform("median")
    df["relative_increase_diff_" + cand_A + "_MAD"] = df.groupby("bucket")[
        "relative_increase_diff_" + cand_A
    ].transform(mad)

    # mediana i mad różnicy względnego wzrostu poparcia
    df["relative_increase_diff_" + cand_B + "_median"] = df.groupby("bucket")[
        "relative_increase_diff_" + cand_B
    ].transform("median")
    df["relative_increase_diff_" + cand_B + "_MAD"] = df.groupby("bucket")[
        "relative_increase_diff_" + cand_B
    ].transform(mad)

    df[cand_A + f"_{new_col_name}"] = (
        df["relative_increase_diff_" + cand_A]
        - df["relative_increase_diff_" + cand_A + "_median"]
    ) / df["relative_increase_diff_" + cand_A + "_MAD"]

    df[cand_B + f"_{new_col_name}"] = (
        df["relative_increase_diff_" + cand_B]
        - df["relative_increase_diff_" + cand_B + "_median"]
    ) / df["relative_increase_diff_" + cand_B + "_MAD"]

    df = df.drop(
        columns=[
            f"{cand_A}_increase",
            f"{cand_B}_increase",
            f"relative_increase_diff_{cand_A}",
            f"relative_increase_diff_{cand_B}",
            f"relative_increase_diff_{cand_A}_median",
            f"relative_increase_diff_{cand_A}_MAD",
            f"relative_increase_diff_{cand_B}_median",
            f"relative_increase_diff_{cand_B}_MAD",
        ]
    )

    return df


def add_anomaly_3(df, cand_A, cand_B, new_col_name="flip"):
    # mediana w grupie
    df[cand_A + "_median_r2"] = df.groupby("bucket")[cand_A + "_r2"].transform("median")
    df[cand_B + "_median_r2"] = df.groupby("bucket")[cand_B + "_r2"].transform("median")

    # wieksza mediana w grupie
    df["higher_median_" + cand_A] = (
        df[cand_A + "_median_r2"] > df[cand_B + "_median_r2"]
    ).astype(bool)
    df["higher_median_" + cand_B] = (
        df[cand_B + "_median_r2"] > df[cand_A + "_median_r2"]
    ).astype(bool)

    df[cand_A + f"_{new_col_name}"] = df["higher_median_" + cand_B] & (
        df[cand_A + "_r2"] > df[cand_B + "_r2"]
    )
    df[cand_B + f"_{new_col_name}"] = df["higher_median_" + cand_A] & (
        df[cand_B + "_r2"] > df[cand_A + "_r2"]
    )

    df = df.drop(
        columns=[
            f"{cand_A}_median_r2",
            f"{cand_B}_median_r2",
            # f"higher_median_{cand_A}",
            # f"higher_median_{cand_B}",
        ]
    )

    return df


def generate_candidate_outliers(df, cand, opponent, k):
    # Define dynamic column names
    k_score_1_col = f"{cand}_k_score_1"
    k_score_2_col = f"{cand}_k_score_2"
    flip_col = f"{cand}_flip"
    more_votes_col = f"{cand}_more_votes"

    # Columns to keep (static + candidate-specific)
    cols_to_keep = [
        "teryt_gmina",
        "polling_station_id",
        "postal_code",
        "postal_clean",
        "bucket",
        f"{cand}_r1",
        f"{cand}_r2",
        f"{opponent}_r1",
        f"{opponent}_r2",
    ]

    # Create result DataFrame with selected columns
    result = df[cols_to_keep].copy()

    # Add boolean outlier columns
    result["pop_outlier"] = df[k_score_1_col] > k
    result["growth_outlier"] = df[k_score_2_col] > k
    result["flip"] = df[flip_col].astype(bool)
    result["more_votes"] = df[more_votes_col].astype(bool)

    return result


def assign_top_anomaly(row):
    if row["more_votes"]:
        return "more_votes"
    elif row["flip"]:
        return "flip"
    elif row["growth_outlier"]:
        return "growth_outlier"
    elif row["pop_outlier"]:
        return "pop_outlier"
    else:
        return None  # or "" if you want empty string


def add_median_corrected_votes(df, cand, opponent):
    # flag_col = f"higher_median_{cand}"
    cand_median_col = f"{cand}_median_r2"
    opponent_median_col = f"{opponent}_median_r2"
    cand_r2 = f"{cand}_r2"
    opponent_r2 = f"{opponent}_r2"

    df = df.copy()

    # Total original valid votes per row
    original_total = df[cand_r2] + df[opponent_r2]

    # Total median-based votes (not yet scaled)
    median_total = df[cand_median_col] + df[opponent_median_col]

    # Scaling factor to preserve total number of votes
    scale = original_total / median_total

    scaled_cand = df[cand_median_col] * scale
    scaled_opponent = df[opponent_median_col] * scale
    total_votes = df[f"{cand}_r2"] + df[f"{opponent}_r2"]

    # Apply rounding while preserving total votes per row
    def round_preserve_total(row):
        a = row["scaled_cand"]
        total = row["total_votes"]
        a_rounded = int(round(a))
        b_rounded = total - a_rounded
        return pd.Series([a_rounded, b_rounded])

    # Temporary scaled values
    df["scaled_cand"] = scaled_cand
    df["scaled_opponent"] = scaled_opponent
    df["total_votes"] = total_votes

    # Assign corrected and rounded votes
    df[[f"{cand}_corrected_r2", f"{opponent}_corrected_r2"]] = df.apply(
        round_preserve_total, axis=1
    )

    # Clean up temporary columns
    df.drop(columns=["scaled_cand", "scaled_opponent", "total_votes"], inplace=True)

    return df


def summarize_by_anomaly(df, cand, opponent):
    anomalies = ["pop_outlier", "growth_outlier", "flip", "more_votes"]
    summary_rows = []

    cand_corr_col = f"{cand}_corrected_r2"
    opponent_corr_col = f"{opponent}_corrected_r2"

    for anomaly in anomalies:
        # Filter rows where 'anomalies' column contains this anomaly string
        filtered = df[df["anomalies"].fillna("").str.contains(anomaly)]

        cand_sum = filtered[f"{cand}_r2"].sum()
        opponent_sum = filtered[f"{opponent}_r2"].sum()
        cand_corr_sum = filtered[cand_corr_col].sum(skipna=True)
        opponent_corr_sum = filtered[opponent_corr_col].sum(skipna=True)

        diff_before = cand_sum - opponent_sum
        diff_after = cand_corr_sum - opponent_corr_sum

        row = {
            "flaga": anomaly,
            "liczba": len(filtered),
            f"głosy {cand}": cand_sum,
            f"głosy {opponent}": opponent_sum,
            "różnica przed": diff_before,
            f"głosy {cand} po": cand_corr_sum,
            f"głosy {opponent} po": opponent_corr_sum,
            "różnica po": diff_after,
            "zmiana": diff_after - diff_before,
        }
        summary_rows.append(row)

    # Create DataFrame
    summary_df = pd.DataFrame(summary_rows)

    # Add "łącznie" row as sum of numeric columns
    total_row = summary_df.select_dtypes(include="number").sum()
    total_row["flaga"] = "łącznie"
    summary_df = pd.concat([summary_df, pd.DataFrame([total_row])], ignore_index=True)

    return summary_df
