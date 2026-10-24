import sys
from pathlib import Path

# Define paths here for easy import
PROJ_ROOT = Path().resolve()
APP_ROOT = PROJ_ROOT / "btc_agent"


MODELS_DIR = APP_ROOT / "models"
DIRECTION_MODEL_DIR = MODELS_DIR / "direction"
VOLATILITY_MODEL_DIR = MODELS_DIR / "volatility"

