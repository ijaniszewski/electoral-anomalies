import pandas as pd
from collections import defaultdict

MIN_SIZE = 10
MAX_SIZE = 16


# def clean_polling_data(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Apply filters described in section 2.1 of the methodology:
#     - drop records without valid postal codes or teryt identifiers
#     - ensure eligible voters and ballots_cast are > 0
#     - ballots_cast >= valid_votes
#     """
#     df = df.copy()
#     df = df[df["postal_code"].notna()]
#     df = df[df["teryt_powiat"].notna()]
#     df = df[(df["eligible_voters"] > 0) & (df["ballots_cast"] > 0)]
#     df = df[df["ballots_cast"] >= df["valid_votes"]]
#     return df


def cluster_by_postal_prefix(df: pd.DataFrame, min_size=10, max_size=16):
    df = df.copy()
    assigned = pd.Series(False, index=df.index)
    groups = []

    def recursive_split(group_df, prefix_len):
        if prefix_len >= 5:
            return []  # can't split further

        split_groups = []
        grouped = group_df.groupby(group_df["postal_code"].str[: prefix_len + 1])
        for _, sub_group in grouped:
            size = len(sub_group)
            if min_size <= size <= max_size:
                split_groups.append(sub_group.copy())
            elif size > max_size:
                split_groups += recursive_split(sub_group, prefix_len + 1)
        return split_groups

    small_groups = []

    for prefix_len in range(2, 6):
        grouped = df[~assigned].groupby(df["postal_code"].str[:prefix_len])
        for _, group in grouped:
            size = len(group)
            if min_size <= size <= max_size:
                groups.append(group.copy())
                assigned.loc[group.index] = True
            elif size > max_size:
                subgroups = recursive_split(group, prefix_len)
                for sg in subgroups:
                    groups.append(sg)
                    assigned.loc[sg.index] = True
            elif size < min_size:
                small_groups.append(group)

    # Still need to merge small groups — placeholder
    leftovers = df[~assigned]
    return groups, leftovers


def assign_cluster_ids(groups: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Add a 'cluster_id' column to each grouped polling station and return merged DataFrame.
    """
    cluster_dfs = []
    for i, group in enumerate(groups):
        group = group.copy()
        group["cluster_id"] = i
        cluster_dfs.append(group)
    return pd.concat(cluster_dfs, ignore_index=True)


def cluster_polling_stations(df: pd.DataFrame):
    """
    Run full clustering pipeline:
    - clean
    - cluster
    - assign IDs
    """
    groups, leftovers = cluster_by_postal_prefix(df)
    clustered = assign_cluster_ids(groups)

    print(f"✅ Total clusters created: {len(groups)}")
    print(f"✅ Total polling stations clustered: {len(clustered)}")
    print(f"⚠️  Leftover stations: {len(leftovers)}")

    return clustered, leftovers
