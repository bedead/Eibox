from datetime import datetime
import logging
import os
from typing import Optional


def _basic_config() -> None:
    # e.g. [2023-10-05 14:12:26 - ama.groq:818 - DEBUG] HTTP Request: POST http://127.0.0.1:4010/foo/bar "200 OK"
    logging.basicConfig(
        format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
    )


def _get_log_filename() -> str:
    """Generate a valid log filename using current timestamp"""
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return f"./logs/{timestamp}.log"


def setup_logging(
    log_type: Optional[str] = None, log_file: Optional[str] = None
) -> logging.Logger:
    logger: logging.Logger = logging.getLogger()
    logger.propagate = False  # Prevents double logging in root logger
    _basic_config()

    env = log_type or os.environ.get("LOG_TYPE")
    print(f"log env: {env}")
    file_path = log_file or os.environ.get("LOG_FILE_PATH", _get_log_filename())
    fh = logging.FileHandler(filename=file_path)
    ch = logging.StreamHandler()

    if env == "debug":
        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    elif env == "info":
        logger.setLevel(logging.INFO)
        fh.setLevel(logging.DEBUG)
        ch.setLevel(logging.INFO)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
