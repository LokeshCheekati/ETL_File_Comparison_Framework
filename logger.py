"""Application logger. Creates a new timestamped log for every run."""

import logging
from pathlib import Path
from datetime import datetime

import config

Path(config.LOG_FOLDER).mkdir(parents=True, exist_ok=True)

log_file = (
    Path(config.LOG_FOLDER)
    / f"{Path(config.LOG_FILE).stem}_{datetime.now():%Y%m%d_%H%M%S}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%d-%b-%Y %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Log file: {log_file}")
