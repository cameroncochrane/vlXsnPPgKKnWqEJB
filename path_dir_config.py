# Add path/directory variables here 
# e.g DATA_DIR = "data"
# RAW_DATA_DIR = DATA_DIR / "raw"

# Project root:
from pathlib import Path
PROJ_ROOT = Path().resolve() 

# Data:
DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"