"""
Entry point for the ETL File Comparison Framework.
"""

from pathlib import Path

import config
from file_reader import read_config, read_data_file
from comparator import compare_data
from report_generator import generate_report
from logger import logger


def main():
    """
    Reads the configuration, executes all active comparisons
    and generates the comparison report.
    """

    logger.info("ETL File Comparison Framework started.")

    try:
        comparison_df = read_config(config.CONFIG_FILE)

    except Exception as ex:
        logger.error(ex)
        return

    all_results = []

    for _, row in comparison_df.iterrows():

        try:

            comparison_name = row["COMPARISON_NAME"]
            source_file = row["SOURCE_FILE"]
            target_file = row["TARGET_FILE"]

            file_delimiter = row["FILE_DELIMITER"]

            key_columns = [
                column.strip()
                for column in row["KEY_COLUMNS"].split(",")
            ]

            compare_columns = row["COMPARE_COLUMNS"]

            source_path = Path(config.SOURCE_FOLDER) / source_file
            target_path = Path(config.TARGET_FOLDER) / target_file

            source_df = read_data_file(
                source_path,
                file_delimiter
            )

            target_df = read_data_file(
                target_path,
                file_delimiter
            )

            comparison_result = compare_data(
                source_df,
                target_df,
                source_file,
                target_file,
                comparison_name,
                key_columns,
                compare_columns
            )

            all_results.append(comparison_result)

        except Exception as ex:

            logger.error(
                f"{comparison_name}: {ex}"
            )

            continue

    generate_report(all_results)

    logger.info("ETL File Comparison Framework completed successfully.")


if __name__ == "__main__":
    main()