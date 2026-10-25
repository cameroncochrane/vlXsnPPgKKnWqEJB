from pathlib import Path

# Define paths here for easy import. Everything the app needs lives inside the btc_agent directory, and paths are built
# from this file's location (btc_agent/src/paths.py), so they're correct whatever directory the app is started from.
APP_ROOT = Path(__file__).resolve().parents[1] # The btc_agent directory

MODELS_DIR = APP_ROOT / "models"
DIRECTION_MODEL_DIR = MODELS_DIR / "direction"
VOLATILITY_MODEL_DIR = MODELS_DIR / "volatility"

DB_DIR = APP_ROOT / "databases"
DB_PATH = DB_DIR / "trading.db"

LOG_DIR = APP_ROOT / "logs"
LOG_PATH = LOG_DIR / "btc_agent.log"
