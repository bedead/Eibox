from datetime import datetime
import logging
import os
from typing import Optional
from dotenv import load_dotenv
from app.core.config import settings

load_dotenv()


def _get_log_filename(log_folder_name: str) -> str:
    """Generate a valid log filename using current timestamp"""
    os.makedirs(log_folder_name, exist_ok=True)  # ensure folder exists
    timestamp = datetime.now().strftime("DATE-%Y-%m-%d_TIME-%H-%M-%S")
    return os.path.join(log_folder_name, f"{timestamp}.log")


def setup_logging(
    log_type: Optional[str] = None, log_folder_name: Optional[str] = None
) -> logging.Logger:
    # Clear duplicate handlers
    root_logger = logging.getLogger("Eibox")

    # Formatter (now using module name instead of root)
    formatter = logging.Formatter(
        fmt="[%(asctime)s - %(name)s:%(filename)s:%(lineno)d - %(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    timestamp = "DATE-19-08-2025-TIME-1:06PM"
    file_path = os.path.join(log_folder_name, f"{timestamp}.log")
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    if log_type == "debug":
        fh.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else:
        fh.setLevel(logging.DEBUG)  # keep full logs in file
        ch.setLevel(logging.INFO)

    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    # Only for initial confirmation
    root_logger.info(f"Logging initialized with level={log_type}, file={file_path}")

    return root_logger


logger = setup_logging(
    log_type=settings.LOG_TYPE, log_folder_name=settings.LOG_FOLDER_NAME
)
