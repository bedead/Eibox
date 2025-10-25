from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from app.core import settings

load_dotenv()


def _get_log_filename(log_folder_name: str) -> str:  # type: ignore
    """Generate a valid log filename using current timestamp"""
    os.makedirs(log_folder_name, exist_ok=True)  # ensure folder exists
    timestamp = datetime.now().strftime("DATE-%Y-%m-%d_TIME-%H-%M-%S")
    return os.path.join(log_folder_name, f"{timestamp}.log")


def setup_logging() -> logging.Logger:
    log_folder_name: str = settings.LOG_FOLDER_NAME
    log_type: str = settings.LOG_TYPE

    root_logger = logging.getLogger("Eibox")
    root_logger.propagate = False  # prevent duplicate logs

    # Clear duplicate handlers if any (important when re-running in dev)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Always allow all logs to propagate
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="[%(asctime)s - %(name)s:%(filename)s:%(lineno)d - %(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Get Logging File Name based on Dev or Prod Server
    os.makedirs(log_folder_name, exist_ok=True)
    if log_type == "debug":
        file_path = os.path.join(log_folder_name, "debug.log")
    elif log_type == "info":
        file_path = _get_log_filename(log_folder_name)
    else:
        file_path = os.path.join(log_folder_name, "default.log")

    # File handler (always DEBUG)
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    # Console handler (level based on log_type)
    ch = logging.StreamHandler()
    ch_level = logging.DEBUG if log_type == "debug" else logging.INFO
    ch.setLevel(ch_level)
    ch.setFormatter(formatter)

    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    return root_logger


logger = setup_logging()
logger.debug(f"Logging initialized with level={settings.LOG_TYPE}")
