import os
import sys

from loguru import logger

# Config
LOG_FOLDER = "./logs"
LOG_LEVEL = "DEBUG"
ERROR_LEVEL = "ERROR"
FILE_ROTATE_FREQUENCY = "00:00"
FILE_ROTATE_MAX_LOGS = 10
PRETTY_PRINT = True

# Ensure logs folder exists
os.makedirs(LOG_FOLDER, exist_ok=True)
if not os.access(LOG_FOLDER, os.W_OK):
    print("Log folder is not writable")
    sys.exit(1)

def configure_loguru():
    logger.remove()

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level=LOG_LEVEL,
        colorize=PRETTY_PRINT,
    )

    # Logs for levels below ERROR
    general_log_path = os.path.join(LOG_FOLDER, "app-{time:YYYY-MM-DD}.log")
    logger.add(
        general_log_path,
        rotation=FILE_ROTATE_FREQUENCY,
        retention=f"{FILE_ROTATE_MAX_LOGS}d",
        compression="zip",
        level=LOG_LEVEL,
        filter=lambda record: record["level"].no < logger.level(ERROR_LEVEL).no,
        backtrace=True,
        diagnose=True,
    )

    # Logs for ERROR and CRITICAL
    error_log_path = os.path.join(LOG_FOLDER, "error-{time:YYYY-MM-DD}.log")
    logger.add(
        error_log_path,
        rotation=FILE_ROTATE_FREQUENCY,
        retention=f"{FILE_ROTATE_MAX_LOGS}d",
        compression="zip",
        level=ERROR_LEVEL,
        backtrace=True,
        diagnose=True,
    )

