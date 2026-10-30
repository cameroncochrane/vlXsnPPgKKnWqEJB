# Modules:
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, TransformerMixin
from modelling.src.bta_functions import add_direction

# Paths:
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "experimentation" / "raw" / "btcusd_data.pkl"

data = pd.read_pickle(RAW_DATA_PATH)

# Add label (Direction_20):
data_20 = add_direction(data=data, shift=20, price="Close")

# X, y separation + temporal train-test-Split:
X = data_20.drop(columns=["Direction_20"])
y = data_20["Direction_20"]
split_idx = int(len(X) * 0.8)
val_idx = int(split_idx * 0.8)
X_train, X_val, X_test = X.iloc[:val_idx], X.iloc[val_idx:split_idx], X.iloc[split_idx:]
y_train, y_val, y_test = y.iloc[:val_idx], y.iloc[val_idx:split_idx], y.iloc[split_idx:]

# Create the lookback features:
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

lookback = 48

# Overall pipeline
process_pipeline = Pipeline([
    ("columns", ColumnTransformer([("close", "passthrough", ["Close"])], remainder="drop")),
    ("scaler", StandardScaler()),
    ("rolling", RollingWindowTransformer(lookback=lookback)) 
])

# Apply pipeline:
X_train_seq = process_pipeline.fit_transform(X_train)
X_val_seq = process_pipeline.transform(X_val)
X_test_seq = process_pipeline.transform(X_test)

# Allign y properly:
y_train_seq = np.asarray(y_train)[lookback - 1:]
y_val_seq = np.asarray(y_val)[lookback - 1:]
y_test_seq = np.asarray(y_test)[lookback - 1:]