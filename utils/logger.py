import logging
import os
from pathlib import Path

try:  # use local config if present
    from config import LOGGING_LEVEL
except ImportError:  # fallback to example config
    from config_example import LOGGING_LEVEL

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "bot_errors.log"

logging.basicConfig(
    level=LOGGING_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("telegram_case_bot")
