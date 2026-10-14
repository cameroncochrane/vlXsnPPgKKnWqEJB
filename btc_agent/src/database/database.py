# This is where the databases will be created and logic regarding their updates placed (SQLAlchemy and JSON):

# Base imports:
from pathlib import Path
import sqlalchemy

APP_ROOT = Path(__file__).resolve().parents[2] # APP_ROOT not PROJ_ROOT
DB_DIR = APP_ROOT / "databases"
DB_PATH = DB_DIR / "trading.db"


def get_engine(db_dir=DB_DIR, db_path=DB_PATH):
    """Create the database (on first run) or connect to the existing one at a specified path in a specified directory."""
    db_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    # SQLite creates the file automatically if it does not exist
    return sqlalchemy.create_engine(f"sqlite:///{db_path}")



