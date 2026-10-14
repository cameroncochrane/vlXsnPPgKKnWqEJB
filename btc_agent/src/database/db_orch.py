"""Inspect and test the trading database."""

from pathlib import Path
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.engine.reflection import Inspector

from database import get_engine

# Define paths:
APP_ROOT = Path(__file__).resolve().parents[2] # APP_ROOT not PROJ_ROOT
DB_DIR = APP_ROOT / "databases"
DB_PATH = DB_DIR / "trading.db"
