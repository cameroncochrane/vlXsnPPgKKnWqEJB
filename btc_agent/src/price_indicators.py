from typing import TypedDict
from numpy.typing import ArrayLike, NDArray
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


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

