# Make price direction and volatility directions using the trained models

import joblib
from pathlib import Path
from typing import Any, Union

from tensorflow import keras
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted


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


# Custom transformers used in pipeline(s):

# Function to generate lag features in a pipeline:
class RollingWindowTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, lookback=96):
        self.lookback = lookback

    def fit(self, X, y=None):
        X = np.asarray(X)
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        check_is_fitted(self)

        X = np.asarray(X, dtype=np.float32)

        if X.ndim != 2:
            raise ValueError("X must be 2D")

        if X.shape[1] != self.n_features_in_:
            raise ValueError("Number of features has changed")

        if not 1 <= self.lookback <= len(X):
            raise ValueError("Invalid lookback")

        return np.stack([
            X[i:i + self.lookback]
            for i in range(len(X) - self.lookback + 1)
        ])