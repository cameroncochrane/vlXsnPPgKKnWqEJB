from typing import TypedDict
from numpy.typing import ArrayLike, NDArray
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

from project_paths import RAW_DATA_DIR


# Data fetch (yfinance):
def fetch_historical_BTCUSD(period: str = "max", save_pkl: bool = True, save_path: str | Path = RAW_DATA_DIR / "btc_usd.pkl") -> pd.DataFrame:
    """Download daily BTC-USD history and optionally save it as a pickle.

    Downloads data from Yahoo Finance, flattens multi-index columns if needed,
    and returns a DataFrame with a date column and price columns.

    Args:
        period: Yahoo Finance lookback period, such as ``"1y"`` or ``"max"``.
        save_pkl: Whether to save the downloaded DataFrame.
        save_path: Destination path used when ``save_pkl`` is true.

    Returns:
        The downloaded BTC-USD history as a DataFrame.

    Raises:
        RuntimeError: If Yahoo Finance returns no historical data.

    Examples:
        Download and save the maximum available history:
        ``history = fetch_historical_BTCUSD()``

        Download one year of history without saving:
        ``recent_history = fetch_historical_BTCUSD(period="1y", save_pkl=False)``
    """
    data = yf.download("BTC-USD", period=period, interval="1d")

    if data.empty:
        raise RuntimeError("Yahoo Finance returned no BTC-USD historical data.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()
    print(f"DataFrame memory usage: {data.memory_usage(deep=True).sum() / 1024**2:.2f} MiB")

    if save_pkl:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data.to_pickle(path)
        print(f"Saved data to {path}")

    return data

def fetch_live_BTCUSD() -> pd.DataFrame:
    """Fetch the latest available BTC-USD quote or intraday bar from Yahoo Finance.

    Returns one row with ``Date``, ``Close``, ``High``, ``Low``, ``Open``, and
    ``Volume`` columns. If the fast quote is unavailable, the latest 1-minute
    bar is used; that bar may not be current.

    Example:
        ``live_btc = fetch_live_BTCUSD()``
    """
    ticker = yf.Ticker("BTC-USD")

    try:
        quote = ticker.fast_info
        price = quote.get("last_price")
    except Exception:
        quote = {}
        price = None

    bar = None
    if price is None or pd.isna(price):
        intraday = ticker.history(period="1d", interval="1m")
        if not intraday.empty:
            bar = intraday.iloc[-1]
            price = bar.get("Close")

    if price is None or pd.isna(price):
        raise RuntimeError(
            "Yahoo Finance returned no BTC-USD quote or intraday price. Try again later."
        )

    def quote_or_bar(key: str, quote_key: str) -> float:
        value = quote.get(quote_key, np.nan)
        if value is None or pd.isna(value):
            value = bar.get(key, np.nan) if bar is not None else np.nan
        return value

    return pd.DataFrame([{
        "Date": pd.Timestamp.now(tz="UTC").normalize().tz_localize(None),
        "Close": price,
        "High": quote_or_bar("High", "day_high"),
        "Low": quote_or_bar("Low", "day_low"),
        "Open": quote_or_bar("Open", "open"),
        "Volume": quote_or_bar("Volume", "last_volume"),
    }])


# Add direction:
def add_direction(data: pd.DataFrame, shift: int = 1, price: str = "Close") -> pd.DataFrame:
    """Add an integer label: 1 if the future price is higher, otherwise 0.

    Rows without a future price are left as missing. Example:
    `data = add_direction(raw_data, shift=5)`.
    """
    if shift < 1:
        raise ValueError("shift must be a positive integer")

    result = data.copy()
    future_price = result[price].shift(-shift)
    result[f"Direction_{shift}"] = (
        (future_price > result[price]).astype("Int64").where(future_price.notna())
    )
    return result


# Add technical indicators:
def add_SMA(data: pd.DataFrame, n: int = 7, price: str = "Close") -> pd.DataFrame:
    """Add an n-period simple moving average.

    Example: `data = add_SMA(raw_data, n=7)`
    """
    result = data.copy()
    result[f"SMA_{n}"] = result[price].rolling(window=n, min_periods=n).mean() #1
    return result

def add_EMA(data: pd.DataFrame, n: int = 7, price: str = "Close") -> pd.DataFrame:
    """Add an n-period exponential moving average.

    Example: `data = add_EMA(raw_data, n=7)`
    """
    result = data.copy()
    result[f"EMA_{n}"] = result[price].ewm(span=n, min_periods=n, adjust=False).mean() #1
    return result

def add_ranges(data: pd.DataFrame, n: int = 4, low: str = "Low", high: str = "High") -> pd.DataFrame:
    """Add intraday range (IDR) and n-period average true range (ATR).

    Example: `data = add_ranges(raw_data, n=4)`
    """
    result = data.copy()
    previous_close = result["Close"].shift(1)
    result["IDR"] = result[high] - result[low] #1
    true_range = pd.concat(
        [
            result[high] - result[low],
            (result[high] - previous_close).abs(),
            (result[low] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result[f"ATR_{n}"] = true_range.rolling(window=n, min_periods=n).mean() #1
    return result

def add_RSI(data: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    """Add an n-period RSI calculated with Wilder-style exponential averages.

    Example: `data = add_RSI(raw_data, n=14)`
    """
    result = data.copy()
    change = result["Close"].diff()
    average_gain = change.clip(lower=0).ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    average_loss = -change.clip(upper=0).ewm(alpha=1 / n, min_periods=n, adjust=False).mean()

    rsi = 100 - 100 / (1 + average_gain / average_loss)
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100)
    rsi = rsi.mask((average_loss == 0) & (average_gain == 0), 50)
    result[f"RSI_{n}"] = rsi #1
    return result

def add_MACD(data: pd.DataFrame) -> pd.DataFrame:
    """Add MACD (12/26), its 9-period signal line, and the histogram.

    Example: `data = add_MACD(raw_data)`
    """
    result = data.copy()
    close = result["Close"]
    fast_ema = close.ewm(span=12, min_periods=12, adjust=False).mean()
    slow_ema = close.ewm(span=26, min_periods=26, adjust=False).mean()
    result["MACD"] = fast_ema - slow_ema #1
    result["MACD_signal"] = result["MACD"].ewm(span=9, min_periods=9, adjust=False).mean() #2
    result["MACD_hist"] = result["MACD"] - result["MACD_signal"] #3
    return result


# Model Evaluation:
class BinaryClassifierEvaluation(TypedDict):
    """Result structure returned by :func:`evaluate_binary_classifier`."""

    metrics: dict[str, float]
    confusion_matrix: NDArray[np.int64]
    classification_report: str

def evaluate_binary_classifier(y_test: ArrayLike, y_pred: ArrayLike, y_proba: ArrayLike | None = None, positive_label: object = 1, verbose: bool = True) -> BinaryClassifierEvaluation:
    """Evaluate binary predictions and return classification metrics and reports.

    Args:
        y_test: One-dimensional array-like of true binary class labels.
        y_pred: One-dimensional array-like of predicted binary class labels.
        y_proba: Optional one-dimensional array-like of probabilities for
            ``positive_label``.
        positive_label: The class treated as positive when calculating
            precision, recall, F1, ROC AUC, and log loss.
        verbose: Whether to print the metrics, confusion matrix, and report.

    Returns:
        A dictionary containing a metrics mapping, confusion matrix, and
        scikit-learn classification report.

    Example:
        >>> result = evaluate_binary_classifier(
        ...     [0, 1, 1], [0, 1, 0], [0.1, 0.8, 0.4], verbose=False
        ... )
        >>> result["metrics"]["ROC AUC"]
    """
    y_test = np.asarray(y_test)
    y_pred = np.asarray(y_pred)
    if y_test.ndim != 1 or y_pred.ndim != 1:
        raise ValueError("y_test and y_pred must be one-dimensional.")
    if len(y_test) != len(y_pred):
        raise ValueError("y_test and y_pred must have the same length.")

    labels = np.unique(y_test)
    if len(labels) != 2:
        raise ValueError("y_test must contain exactly two classes.")
    if positive_label not in labels:
        raise ValueError("positive_label must be present in y_test.")

    metrics_dict = {
        "Accuracy": accuracy_score(y_test, y_pred),
        "Balanced Accuracy": balanced_accuracy_score(y_test, y_pred),
        "Precision": precision_score(
            y_test, y_pred, pos_label=positive_label, zero_division=0
        ),
        "Recall": recall_score(
            y_test, y_pred, pos_label=positive_label, zero_division=0
        ),
        "F1 Score": f1_score(
            y_test, y_pred, pos_label=positive_label, zero_division=0
        ),
        "Matthews Corrcoef": matthews_corrcoef(y_test, y_pred),
    }

    if y_proba is not None:
        y_proba = np.asarray(y_proba)
        if y_proba.ndim != 1 or len(y_proba) != len(y_test):
            raise ValueError("y_proba must be one-dimensional and match y_test length.")
        if not np.all(np.isfinite(y_proba)) or np.any((y_proba < 0) | (y_proba > 1)):
            raise ValueError("y_proba must contain finite probabilities in [0, 1].")

        positive_targets = (y_test == positive_label).astype(int)
        metrics_dict["ROC AUC"] = roc_auc_score(positive_targets, y_proba)
        metrics_dict["Log Loss"] = log_loss(
            positive_targets,
            np.column_stack((1 - y_proba, y_proba)),
            labels=[0, 1],
        )

    cm = confusion_matrix(y_test, y_pred)
    clf_report = classification_report(y_test, y_pred, zero_division=0)

    if verbose:
        print("\n===== Binary Classification Evaluation =====\n")
        for metric, value in metrics_dict.items():
            print(f"{metric}: {value:.4f}")
        print("\nConfusion Matrix:")
        print(cm)
        print("\nClassification Report:")
        print(clf_report)

    return {
        "metrics": metrics_dict,
        "confusion_matrix": cm,
        "classification_report": clf_report,
    }