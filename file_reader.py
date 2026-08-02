"""
Reads and validates the configuration file and input data files.
"""

import pandas as pd
from pathlib import Path
from logger import logger
import config

def read_config(config_file):
    """
    Reads the configuration Excel file, validates its contents,
    and returns only the active comparison records.
    """
    logger.info(f"Reading configuration file: {config_file}")

    if not Path(config_file).exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_file}"
        )

    config_df = pd.read_excel(config_file, sheet_name=config.CONFIG_SHEET)

    comparison_df = validate_config(config_df)

    logger.info(
    f"Configuration file loaded successfully. "
    f"Total Active comparisons found: {len(comparison_df)}"
    )

    return comparison_df

# VALIDATING THE CONFIG DATAFRAME
def validate_config(config_df):
    """
    Validates the configuration DataFrame by checking mandatory
    columns and filtering active comparisons.
    """

    mandatory_columns = [
    "COMPARISON_NAME",
    "SOURCE_FILE",
    "TARGET_FILE",
    "FILE_DELIMITER",
    "KEY_COLUMNS"
    ]

    active_df = config_df[
    config_df["RUN_FLAG"] == config.ACTIVE_FLAG
    ]

    logger.info(
    f"Active comparisons found: {len(active_df)}"
    )

    if active_df.empty:
        raise ValueError(
            "No active comparisons found in the configuration file."
        )

    for column in mandatory_columns:
        if column not in active_df.columns:
            raise ValueError(
                f"Mandatory column '{column}' is missing in sheet 'Config'."
            )

    active_df = active_df.fillna("")

    return active_df

def read_data_file(file_path, file_delimiter):
    """
    Reads a delimited source or target data file into a DataFrame.
    """
    logger.info(f"Reading data file: {file_path}")

    if not Path(file_path).exists():
        raise FileNotFoundError(
            f"Data file not found: {file_path}"
        )

    data_df = pd.read_csv(file_path, delimiter = file_delimiter)

    logger.info(
    f"Loaded {len(data_df)} records from {Path(file_path).name}"
    )

    return data_df