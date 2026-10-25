# Make price direction and volatility directions using the trained models

import joblib
from pathlib import Path
from typing import Any, Union

from tensorflow import keras

from src.paths import DIRECTION_MODEL_DIR, VOLATILITY_MODEL_DIR

# Model filenames (for import):
DIRECTION_MODEL_NAME = "process_pipeline.joblib"
DIRECTION_PREPROCESSOR_NAME = "model_simple.keras" 

VOLATILITY_MODEL_NAME = ""
VOLATILITY_PREPROCESSOR_NAME = ""

d_model_path = DIRECTION_MODEL_DIR / DIRECTION_MODEL_NAME
d_preprocessor_path = DIRECTION_MODEL_DIR /DIRECTION_PREPROCESSOR_NAME

v_model_path = VOLATILITY_MODEL_DIR / VOLATILITY_MODEL_NAME
v_model_preprocessor_path = VOLATILITY_MODEL_DIR / VOLATILITY_MODEL_NAME

def load_preprocessor(path: Union[str, Path]) -> Any:
      """Load a serialized preprocessing object from a file.

      Args:
            path: Path to the serialized preprocessor.

      Returns:
            The loaded preprocessing object.
      """
      
      return joblib.load(path)

def load_keras_model(path: Union[str, Path]) -> Any:
      """Load a serialized Keras model from a .keras file.

      Args:
            path: Path to the .keras model file.

      Returns:
            The loaded Keras model.

      Raises:
            FileNotFoundError: If the model file does not exist.
      """

      model_path = Path(path)
      if not model_path.is_file():
            raise FileNotFoundError(f"Keras model not found: {model_path}")
      return keras.models.load_model(model_path)

