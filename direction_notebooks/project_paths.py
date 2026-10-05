from pathlib import Path
import sys

PROJ_ROOT = Path().resolve().parents[0]
project_root = str(PROJ_ROOT)
sys.path.insert(0, project_root)

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Direction modelling:
DCN_DATA_DIR = PROCESSED_DATA_DIR / "direction"

PRE_SPLIT_DATA_DIR = DCN_DATA_DIR / "lr"
PRE_SPLIT_DATA_LR_PATH = PRE_SPLIT_DATA_DIR / "ind_data.pkl" # Pre-split data containing indicators and 'Direction_1' label column