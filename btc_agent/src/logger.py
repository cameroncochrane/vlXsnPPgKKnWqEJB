# Logging set-up shared by main.py, timer.py, app.py and the src modules.

import logging
import logging.handlers

from src.paths import LOG_DIR, LOG_PATH

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """Send log records to btc_agent/logs/btc_agent.log (rotated at 1 MB, 5 old files kept) and to stderr.

    stderr is what journalctl shows when the app runs under systemd; the file keeps a history either way.
    Safe to call more than once (e.g. on every Streamlit rerun): handlers are only added the first time.
    Call it once at the start of each entry point, then get a logger per module with logging.getLogger(__name__).

    Example:
        >>> setup_logging()
        >>> logger = logging.getLogger(__name__)
        >>> logger.error("Something failed")
    """
    root = logging.getLogger()
    if any(getattr(handler, "_btc_agent", False) for handler in root.handlers):
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    stream_handler = logging.StreamHandler()
    for handler in (file_handler, stream_handler):
        handler.setFormatter(formatter)
        handler._btc_agent = True # Marks handlers added here, so repeat calls don't duplicate them
        root.addHandler(handler)
    root.setLevel(level)

    for noisy in ("httpx", "httpcore", "urllib3", "yfinance", "openai", "peewee"): # Third-party libraries that log every request at INFO
        logging.getLogger(noisy).setLevel(logging.WARNING)
