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
