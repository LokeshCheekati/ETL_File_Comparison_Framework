"""
Compares source and target DataFrames and identifies missing records
and column-level data mismatches.
"""

import pandas as pd
from logger import logger


def compare_data(
    source_df,
    target_df,
    source_file,
    target_file,
    comparison_name,
    key_columns,
    compare_columns
):
    """
    Compares two DataFrames and returns the comparison results.
    """

    logger.info(f"Starting comparison: {comparison_name}")

    # Validate that all key columns exist in both DataFrames.
    validate_columns_exist(source_df, key_columns, source_file)
    validate_columns_exist(target_df, key_columns, target_file)

    # Compare all non-key columns when COMPARE_COLUMNS is blank or ALL.
    if compare_columns.strip().upper() in ("", "ALL"):
        columns_to_compare = [
            column
            for column in source_df.columns
            if column not in key_columns
        ]
    else:
        columns_to_compare = [
            column.strip()
            for column in compare_columns.split(",")
        ]

    validate_columns_exist(source_df,columns_to_compare,source_file)
    validate_columns_exist(target_df,columns_to_compare,target_file)

    # Merge source and target using the business key.
    merged_df = pd.merge(
        source_df,
        target_df,
        on=key_columns,
        how="outer",
        indicator=True,
        suffixes=("_SOURCE", "_TARGET")
    )

    # Split merged records into source only, target only and common records.
    source_only_df = merged_df[merged_df["_merge"] == "left_only"]
    target_only_df = merged_df[merged_df["_merge"] == "right_only"]
    common_df = merged_df[merged_df["_merge"] == "both"]

    mismatch_records = []

    # Compare each configured column.
    for column in columns_to_compare:

        source_column = f"{column}_SOURCE"
        target_column = f"{column}_TARGET"

        mismatch_condition = (
            (common_df[source_column] != common_df[target_column])& ~(
                    common_df[source_column].isna()
                    & common_df[target_column].isna()
                    )   
        )

        column_mismatch_df = common_df[mismatch_condition]

        # Capture every mismatched value.
        for _, row in column_mismatch_df.iterrows():

            business_key = ", ".join(
                f"{key}={row[key]}"
                for key in key_columns
            )

            mismatch_records.append(
                {
                    "COMPARISON_NAME": comparison_name,
                    "BUSINESS_KEY": business_key,
                    "COLUMN_NAME": column,
                    "SOURCE": row[source_column],
                    "TARGET": row[target_column]
                }
            )

    mismatch_df = pd.DataFrame(mismatch_records)

    # Determine overall comparison status.
    if (
        source_only_df.empty
        and target_only_df.empty
        and mismatch_df.empty
    ):
        status = "PASS"
    else:
        status = "FAIL"

    logger.info(
        f"{comparison_name} completed. "
        f"Source Only={len(source_only_df)}, "
        f"Target Only={len(target_only_df)}, "
        f"Mismatches={len(mismatch_df)}, "
        f"Status={status}"
    )

    return {
        "comparison_name": comparison_name,
        "source_count": len(source_df),
        "target_count": len(target_df),
        "source_only_df": source_only_df,
        "target_only_df": target_only_df,
        "mismatch_df": mismatch_df,
        "status": status
    }


def validate_columns_exist(data_df, columns, file_name):
    """
    Validates that all specified columns exist in the given DataFrame.
    """

    for column in columns:

        if column not in data_df.columns:
            raise ValueError(
                f"Column '{column}' does not exist in '{file_name}'."
            )