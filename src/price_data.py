from pathlib import Path

PROJ_ROOT = Path().resolve().parents[0]
RAW_DATA_DIR = PROJ_ROOT / "data" / "raw"

import pandas as pd
import numpy as np
import yfinance as yf

# Using yfinance API:

def fetch_historical_BTCUSD(period: str = "max", save_pkl: bool = True, save_path: str | Path = RAW_DATA_DIR / "btc_usd_raw.pkl") -> pd.DataFrame:
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
