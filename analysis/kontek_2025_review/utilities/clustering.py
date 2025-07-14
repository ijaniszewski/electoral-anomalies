from collections import defaultdict

import numpy as np
import pandas as pd


def add_random_buckets(df, n, k_min, k_max, random_state=None):
    """
    Partition a DataFrame into n random groups (buckets), each with at least k_min and at most k_max rows.
    Adds a 'bucket' column to the DataFrame indicating the group assignment.

    Args:
        df (pd.DataFrame): The DataFrame to partition.
        n (int): Number of buckets (groups) to create.
        k_min (int): Minimum number of rows per bucket.
        k_max (int): Maximum number of rows per bucket.
        random_state (int, optional): Seed for reproducibility. Default is None.

    Returns:
        pd.DataFrame: A new DataFrame with a 'bucket' column indicating the group assignment.

    Raises:
        ValueError: If the constraints cannot be satisfied with the given n, k_min, and k_max.
    """
    N = len(df)
    if N < n * k_min or N > n * k_max:
        raise ValueError(
            "Constraints cannot be satisfied with given n, k_min, and k_max."
        )

    # Start with k_min in each bucket
    sizes = np.full(n, k_min)
    remaining = N - sizes.sum()
    increments = np.zeros(n, dtype=int)

    rng = np.random.default_rng(random_state)
    while remaining > 0:
        idxs = np.where(sizes + increments < k_max)[0]
        idx = rng.choice(idxs)
        increments[idx] += 1
        remaining -= 1

    final_sizes = sizes + increments

    # Shuffle the DataFrame
    shuffled_df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    # Assign bucket numbers
    bucket_labels = np.repeat(np.arange(n), final_sizes)
    shuffled_df["bucket"] = bucket_labels

    # Restore original order if needed (optional)
    # shuffled_df = shuffled_df.sort_index()

    return shuffled_df


def print_bucket_stats(df, bucket_col="bucket", range1=(10, 16), range2=(6, 30)):
    """
    Prints statistics about bucket sizes in the DataFrame.
    Shows total number of buckets and how many fall into two specified ranges.

    Args:
        df (pd.DataFrame): DataFrame containing the bucket column.
        bucket_col (str): Name of the column with bucket assignments.
        range1 (tuple): First (min, max) range for bucket size.
        range2 (tuple): Second (min, max) range for bucket size.
    """
    bucket_sizes = df[bucket_col].value_counts()
    total_buckets = bucket_sizes.count()
    buckets_in_range1 = bucket_sizes[
        (bucket_sizes >= range1[0]) & (bucket_sizes <= range1[1])
    ].count()
    buckets_in_range2 = bucket_sizes[
        (bucket_sizes >= range2[0]) & (bucket_sizes <= range2[1])
    ].count()
    print(f"Total buckets: {total_buckets}")
    print(
        f"Buckets with {range1[0]}–{range1[1]} items: {buckets_in_range1} ({buckets_in_range1 / total_buckets:.1%})"
    )
    print(
        f"Buckets with {range2[0]}–{range2[1]} items: {buckets_in_range2} ({buckets_in_range2 / total_buckets:.1%})"
    )


def add_janiszewski_postal_buckets(
    df, min_bucket_size=10, max_bucket_size=16, postal_code_col="postal_code"
):
    """
    Assigns spatially-coherent buckets to a DataFrame based on postal code prefixes, with constraints on bucket size.
    The function mimics the logic from generate_buckets_3.ipynb.

    Args:
        df (pd.DataFrame): Input DataFrame. Must contain a column with postal codes.
        min_bucket_size (int): Minimum number of rows per bucket.
        max_bucket_size (int): Maximum number of rows per bucket.
        postal_code_col (str): Name of the column containing postal codes (e.g., 'postal_code').

    Returns:
        pd.DataFrame: DataFrame with a new 'bucket' column indicating group assignment.
    """
    df = df.copy()
    # Clean postal codes: remove dash, ensure string
    df["postal_clean"] = df[postal_code_col].astype(str).str.replace("-", "")

    # Compute postal code prefixes
    df["postal_2"] = df["postal_clean"].str[:2]
    df["postal_3"] = df["postal_clean"].str[:3]
    df["postal_4"] = df["postal_clean"].str[:4]
    df["postal_5"] = df["postal_clean"]

    # Precompute value counts for each prefix
    df["postal_3_value_count"] = df["postal_3"].map(df["postal_3"].value_counts())
    df["postal_4_value_count"] = df["postal_4"].map(df["postal_4"].value_counts())

    # Step 1: Assign buckets by 3-digit prefix if group size is valid
    postal_3_counts = df["postal_3"].value_counts()
    valid_postals_3 = postal_3_counts[
        (postal_3_counts >= min_bucket_size) & (postal_3_counts <= max_bucket_size)
    ].index
    df["bucket"] = df["postal_3"].where(df["postal_3"].isin(valid_postals_3))

    # Step 2: Assign by 4-digit prefix for unassigned rows
    postal_4_counts = df["postal_4"].value_counts()
    valid_postals_4 = postal_4_counts[
        (postal_4_counts >= min_bucket_size) & (postal_4_counts <= max_bucket_size)
    ].index
    mask_4 = df["bucket"].isna() & df["postal_4"].isin(valid_postals_4)
    df.loc[mask_4, "bucket"] = df.loc[mask_4, "postal_4"]

    # Step 3: Assign by 5-digit (full) postal code for unassigned rows
    postal_5_counts = df["postal_5"].value_counts()
    valid_postals_5 = postal_5_counts[
        (postal_5_counts >= min_bucket_size) & (postal_5_counts <= max_bucket_size)
    ].index
    mask_5 = df["bucket"].isna() & df["postal_5"].isin(valid_postals_5)
    df.loc[mask_5, "bucket"] = df.loc[mask_5, "postal_5"]

    # Step 4: For oversized 5-digit groups, assign if all are ungrouped
    mask_postal_5 = df["bucket"].isna() & (
        (df["postal_3_value_count"] > max_bucket_size)
        | (df["postal_4_value_count"] > max_bucket_size)
    )
    postal_5_counts = df.loc[mask_postal_5, "postal_5"].value_counts()
    for postal_code, count in postal_5_counts.items():
        if count > max_bucket_size:
            same_postal_mask = (df["postal_5"] == postal_code) & df["bucket"].isna()
            if same_postal_mask.sum() == count:
                df.loc[same_postal_mask, "bucket"] = postal_code

    # Step 5: For remaining unassigned, chunk by sorted postal code within 3-digit prefix
    leftovers = df[df["bucket"].isna()].copy()
    for prefix, group in leftovers.groupby("postal_3"):
        group_sorted = group.sort_values(by="postal_clean")
        i = 0
        while i < len(group_sorted):
            chunk = group_sorted.iloc[i : i + max_bucket_size]
            if len(chunk) >= min_bucket_size:
                bucket_id = f"{prefix}_L{i//max_bucket_size}"
                df.loc[chunk.index, "bucket"] = bucket_id
                i += len(chunk)
            else:
                break  # remaining rows too small to form a valid group

    # Step 6: Try to merge final leftovers into existing buckets, else assign fallback
    final_leftovers = df[df["bucket"].isna()].copy()
    existing_buckets = df.dropna(subset=["bucket"]).copy()
    existing_buckets["bucket_size"] = existing_buckets.groupby("bucket")[
        "bucket"
    ].transform("count")
    for prefix, group in final_leftovers.groupby("postal_3"):
        group_sorted = group.sort_values(by="postal_clean")
        existing_in_prefix = (
            existing_buckets[existing_buckets["postal_3"] == prefix]
            .groupby("bucket")
            .first()
        )
        for idx, row in group_sorted.iterrows():
            # Try to append to a not-too-large existing group
            assigned = False
            for bucket_id, b_row in existing_in_prefix.iterrows():
                current_size = df[df["bucket"] == bucket_id].shape[0]
                if current_size < max_bucket_size:
                    df.at[idx, "bucket"] = bucket_id
                    assigned = True
                    break
            # If no spot found, assign a new fallback bucket
            if pd.isna(df.at[idx, "bucket"]):
                fallback_id = f"{prefix}_F{idx}"
                df.at[idx, "bucket"] = fallback_id

    if df["bucket"].isna().sum() > 0:
        # Find all existing buckets and their sizes
        bucket_sizes = df["bucket"].value_counts()
        smallest_buckets = bucket_sizes.nsmallest(10).index  # or all buckets
        for idx in df[df["bucket"].isna()].index:
            # Assign to the bucket with the smallest current size
            target_bucket = df["bucket"].value_counts().idxmin()
            df.at[idx, "bucket"] = target_bucket

    # Optionally, remove buckets with fewer than 3 members
    vc = df["bucket"].value_counts()
    df = df[df["bucket"].isin(vc[vc >= 3].index)]

    # Remove all helper columns before returning
    helper_cols = [
        "postal_clean",
        "postal_2",
        "postal_3",
        "postal_4",
        "postal_5",
        "postal_3_value_count",
        "postal_4_value_count",
    ]
    df = df.drop(columns=[col for col in helper_cols if col in df.columns])

    return df


def add_bialek_postal_buckets(
    df: pd.DataFrame,
    postal_code_col: str = "postal_code",
    min_size: int = 10,
    max_size: int = 16,
) -> pd.DataFrame:
    """
    Returns a copy of df with a new column `group_id` containing the group number
    such that each group has min_size <= n <= max_size (as much as possible).
    Groups are formed by recursively splitting by postal code prefix, then merging small groups.

    Args:
        df (pd.DataFrame): Input DataFrame with a postal code column.
        code_col (str): Name of the column with postal codes (should be int or str, 5 digits).
        min_size (int): Minimum group size.
        max_size (int): Maximum group size.

    Returns:
        pd.DataFrame: Copy of df with a new 'group_id' column.
    """
    df["postal_clean"] = df[postal_code_col].astype(str).str.replace("-", "")
    work = df.copy()
    work["_code_str"] = work["postal_clean"].astype(str).str.zfill(5)

    accepted = {}  # {prefix: list[index]}
    small = {}  # prefixy < min_size (to be merged later)

    # 1. Recursive splitting of large groups
    def split(prefix: str, idxs: list[int], depth: int):
        size = len(idxs)
        # a) Acceptable group
        if min_size <= size <= max_size or depth == 5:
            accepted[prefix] = idxs
            return
        # b) Too small – save for later merging
        if size < min_size:
            small[prefix] = idxs
            return
        # c) Too large – split deeper
        next_depth = depth + 1
        sub_prefixes = work.loc[idxs, "_code_str"].str[:next_depth]
        for sub_pref, sub_idxs in work.loc[idxs].groupby(sub_prefixes).groups.items():
            split(sub_pref, list(sub_idxs), next_depth)

    # Start with 2-digit prefixes
    for pref2, grp in work.groupby(work["_code_str"].str[:2]).groups.items():
        split(pref2, list(grp), depth=2)

    # 2. Merge small groups within the same 2-digit prefix
    buckets = defaultdict(list)  # {pref2: [(pref, idxs), ...]}
    for p, idxs in small.items():
        buckets[p[:2]].append((p, idxs))

    for pref2, lst in buckets.items():
        # Sort by prefix value for spatial proximity
        lst.sort(key=lambda x: int(x[0]))
        buf_idx, buf_pref = [], []
        for p, idxs in lst:
            buf_idx.extend(idxs)
            buf_pref.append(p)
            if len(buf_idx) >= min_size:
                # If > max_size, split into chunks
                while len(buf_idx) > max_size:
                    accepted[f"{pref2}_{len(accepted)}"] = buf_idx[:max_size]
                    buf_idx = buf_idx[max_size:]
                accepted["+".join(buf_pref)] = buf_idx
                buf_idx, buf_pref = [], []
        # Remainder < min_size – append to last group for this prefix
        if buf_idx:
            last_keys = [k for k in accepted.keys() if k.startswith(pref2)]
            if last_keys:
                last_key = last_keys[-1]
                accepted[last_key].extend(buf_idx)
            else:
                # If no group exists, create a new one
                accepted[f"{pref2}_rem"] = buf_idx

    # 3. Assign group numbers
    idx2gid = {}
    for gid, (_, lst) in enumerate(accepted.items()):
        for i in lst:
            idx2gid[i] = gid
    work["bucket"] = work.index.map(idx2gid)

    # 4. Remove groups with fewer than 4 members
    group_sizes = work.groupby("bucket").transform("count")["postal_clean"]
    work = work[group_sizes > 3].copy()

    return work.drop(columns="_code_str")
