"""Entry point for the ETL File Comparison Framework."""

import config
from file_reader import read_config, read_data_file, find_latest_file
from comparator import compare_data
from comparison_report import generate_comparison_report
from summary_report import generate_summary_report
from logger import logger


def main():
    logger.info("ETL File Comparison Framework started.")

    try:
        comparison_df = read_config(config.CONFIG_FILE)
    except Exception as ex:
        logger.error(ex)
        return

    all_results = []

    for _, row in comparison_df.iterrows():
        comparison_name = str(row["COMPARISON_NAME"]).strip()

        try:
            configured_source_file = str(row["SOURCE_FILE"]).strip()
            configured_target_file = str(row["TARGET_FILE"]).strip()
            file_delimiter = row["FILE_DELIMITER"]

            key_columns = [
                column.strip()
                for column in str(row["KEY_COLUMNS"]).split(",")
                if column.strip()
            ]
            compare_columns = str(row.get("COMPARE_COLUMNS", ""))

            # Exact filename -> exact file.
            # Prefix/pattern -> latest matching file.
            source_path = find_latest_file(
                config.SOURCE_FOLDER,
                configured_source_file
            )
            target_path = find_latest_file(
                config.TARGET_FOLDER,
                configured_target_file
            )

            # These are the actual files used by the comparison/report.
            source_file = source_path.name
            target_file = target_path.name

            source_df = read_data_file(source_path, file_delimiter)
            target_df = read_data_file(target_path, file_delimiter)

            comparison_result = compare_data(
                source_df,
                target_df,
                source_file,
                target_file,
                comparison_name,
                key_columns,
                compare_columns
            )

            comparison_result["source_file"] = source_file
            comparison_result["target_file"] = target_file

            all_results.append(comparison_result)

            # Generate the detailed report immediately.
            # Only the compact result metadata is retained for the final summary.
            generate_comparison_report(comparison_result)

        except Exception as ex:
            logger.error(f"{comparison_name}: {ex}")
            continue

    if all_results:
        generate_summary_report(all_results)
    else:
        logger.warning("No comparisons completed successfully. Summary report was not generated.")

    logger.info("ETL File Comparison Framework completed successfully.")


if __name__ == "__main__":
    main()
