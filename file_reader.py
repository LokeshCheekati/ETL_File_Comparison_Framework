"""Reads configuration/data files and resolves exact or latest input files."""

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from logger import logger
import config


def read_config(config_file):
    logger.info(f"Reading configuration file: {config_file}")

    if not Path(config_file).exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    config_df = pd.read_excel(config_file, sheet_name=config.CONFIG_SHEET)
    comparison_df = validate_config(config_df)

    logger.info(
        f"Configuration file loaded successfully. "
        f"Total Active comparisons found: {len(comparison_df)}"
    )
    return comparison_df


def validate_config(config_df):
    mandatory_columns = [
        "COMPARISON_NAME",
        "SOURCE_FILE",
        "TARGET_FILE",
        "FILE_DELIMITER",
        "KEY_COLUMNS",
    ]

    if "RUN_FLAG" not in config_df.columns:
        raise ValueError("Mandatory column 'RUN_FLAG' is missing in sheet 'Config'.")

    active_df = config_df[config_df["RUN_FLAG"] == config.ACTIVE_FLAG]

    logger.info(f"Active comparisons found: {len(active_df)}")

    if active_df.empty:
        raise ValueError("No active comparisons found in the configuration file.")

    for column in mandatory_columns:
        if column not in active_df.columns:
            raise ValueError(
                f"Mandatory column '{column}' is missing in sheet 'Config'."
            )

    if "COMPARE_COLUMNS" not in active_df.columns:
        active_df["COMPARE_COLUMNS"] = ""

    return active_df.fillna("")


def _filename_regex(configured_name):
    """Build regex for prefix/pattern matching after exact-file check."""
    value = str(configured_name).strip()

    # Supported variable tokens.  &LY&M represents a six-digit YYYYMM portion.
    token_patterns = {
        "&YYYY": r"\d{4}",
        "&LY": r"\d{4}",
        "&YY": r"\d{2}",
        "&MM": r"\d{2}",
        "&M": r"\d{2}",
        "&DD": r"\d{2}",
        "&HH": r"\d{2}",
        "&MI": r"\d{2}",
        "&SS": r"\d{2}",
    }

    parts = []
    i = 0
    while i < len(value):
        matched = False
        for token in sorted(token_patterns, key=len, reverse=True):
            if value.startswith(token, i):
                parts.append(token_patterns[token])
                i += len(token)
                matched = True
                break
        if not matched:
            parts.append(re.escape(value[i]))
            i += 1

    return re.compile(r"^" + "".join(parts) + r".*$", re.IGNORECASE)


def _parse_filename_datetime(filename):
    """Extract common date/time formats from a filename."""
    name = Path(filename).stem

    patterns = [
        (r"(?<!\d)(20\d{2})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})(?!\d)", "%Y%m%d_%H%M%S"),
        (r"(?<!\d)(20\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(?!\d)", "%Y%m%d%H%M%S"),
        (r"(?<!\d)(20\d{2})[-_](\d{2})[-_](\d{2})[_-](\d{2})[_-](\d{2})[_-](\d{2})(?!\d)", "%Y-%m-%d_%H-%M-%S"),
        (r"(?<!\d)(20\d{2})[-_](\d{2})[-_](\d{2})(?!\d)", "%Y-%m-%d"),
        (r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)", "%Y%m%d"),
        (r"(?<!\d)(20\d{2})[-_](\d{2})(?!\d)", "%Y-%m"),
        (r"(?<!\d)(20\d{2})(\d{2})(?!\d)", "%Y%m"),
    ]

    for pattern, fmt in patterns:
        match = re.search(pattern, name)
        if not match:
            continue
        value = match.group(0)
        if fmt in ("%Y-%m-%d", "%Y-%m"):
            value = value.replace("_", "-")
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    return None


def find_latest_file(folder, configured_name):
    """
    Resolve an input file.

    Exact existing filename always wins. Otherwise configured_name is treated
    as a prefix/pattern and the latest dated matching file is selected.
    If no matching filename contains a date, latest modified file is used.
    """
    folder = Path(folder)
    configured_name = str(configured_name).strip()

    if not folder.exists():
        raise FileNotFoundError(f"Input folder not found: {folder}")

    exact_path = folder / configured_name
    if exact_path.is_file():
        logger.info(f"Using exact file: {exact_path.name}")
        return exact_path

    pattern = _filename_regex(configured_name)
    matching_files = [
        file for file in folder.iterdir()
        if file.is_file() and pattern.match(file.name)
    ]

    if not matching_files:
        raise FileNotFoundError(
            f"No files found in '{folder}' matching '{configured_name}'."
        )

    logger.info(
        f"{len(matching_files)} file(s) found for prefix/pattern '{configured_name}'"
    )

    dated_files = []
    for file in matching_files:
        file_datetime = _parse_filename_datetime(file.name)
        if file_datetime is not None:
            dated_files.append((file, file_datetime))

    if dated_files:
        latest_file, latest_datetime = max(
            dated_files,
            key=lambda item: (item[1], item[0].stat().st_mtime)
        )
        logger.info(
            f"Selected latest dated file: {latest_file.name}"
        )
        return latest_file

    logger.warning(
        f"No date found in filenames for '{configured_name}'. "
        "Using latest modified file."
    )

    latest_file = max(
        matching_files,
        key=lambda file: file.stat().st_mtime
    )
    logger.info(f"Selected latest modified file: {latest_file.name}")
    return latest_file


def read_data_file(file_path, file_delimiter):
    logger.info(f"Reading data file: {file_path}")

    if not Path(file_path).exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    data_df = pd.read_csv(file_path, delimiter=file_delimiter)

    logger.info(
        f"Loaded {len(data_df)} records from {Path(file_path).name}"
    )
    return data_df
