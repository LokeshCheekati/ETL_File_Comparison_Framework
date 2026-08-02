"""
Configures the application logger used across the ETL File Comparison Framework.
"""

import logging
from pathlib import Path

import config

# Create the logs directory if it doesn't already exist.
Path(config.LOG_FOLDER).mkdir(parents=True, exist_ok=True)

log_file = Path(config.LOG_FOLDER) / config.LOG_FILE

# Configure the application logger.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%d-%b-%Y %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Shared logger instance for all project modules.
logger = logging.getLogger(__name__)