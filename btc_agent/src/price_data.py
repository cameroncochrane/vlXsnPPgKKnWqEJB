import logging
from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

# Using yfinance API:

def fetch_historical_BTCUSD(period: str = "max") -> pd.DataFrame:
    """Download daily BTC-USD history

    Downloads data from Yahoo Finance, flattens multi-index columns if needed,
    and returns a DataFrame with a date column and price columns.

    Args:
        period: Yahoo Finance lookback period, such as ``"1y"`` or ``"max"``.

    Returns:
        The downloaded BTC-USD history as a DataFrame.

    Raises:
        RuntimeError: If Yahoo Finance returns no historical data.

    Examples:
        Download the maximum available history:
        ``history = fetch_historical_BTCUSD()``

        Download one year of history without saving:
        ``recent_history = fetch_historical_BTCUSD(period="1y")``
    """
    data = yf.download("BTC-USD", period=period, interval="1d")

    if data is None:
        raise RuntimeError("Yahoo Finance returned no BTC-USD historical data.")

    if not isinstance(data, pd.DataFrame):
        raise RuntimeError("Yahoo Finance returned unexpected data for BTC-USD historical data.")

    if data.empty:
        raise RuntimeError("Yahoo Finance returned no BTC-USD historical data.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()
    logger.debug("BTC-USD history memory usage: %.2f MiB", data.memory_usage(deep=True).sum() / 1024**2)

    return data

def fetch_live_BTCUSD() -> pd.DataFrame:
    """Fetch the latest available BTC-USD quote or intraday bar from Yahoo Finance.

    Returns one row with ``QuoteTime``, ``Close``, ``High``, ``Low``,
    ``Open``, and ``Volume`` columns. If the fast quote is unavailable, the
    latest 1-minute bar is used; that bar may not be current.

    Example:
        ``live_btc = fetch_live_BTCUSD()``
    """
    ticker = yf.Ticker("BTC-USD")
    quote_time = None

    try:
        quote = ticker.fast_info
        price = quote.get("last_price")
        for key in ("last_trade_time", "last_update", "last_updated", "timestamp"):
            value = quote.get(key)
            if value is not None and not pd.isna(value):
                quote_time = value
                break
    except Exception:
        quote = {}
        price = None

    bar = None
    if price is None or pd.isna(price):
        intraday = ticker.history(period="1d", interval="1m")
        if not intraday.empty:
            bar = intraday.iloc[-1]
            price = bar.get("Close")
            if quote_time is None:
                quote_time = bar.name

    if price is None or pd.isna(price):
        raise RuntimeError(
            "Yahoo Finance returned no BTC-USD quote or intraday price. Try again later."
        )

    if quote_time is None:
        quote_time = pd.Timestamp.now(tz="UTC").tz_localize(None)

    def normalize_ts(ts):
        if ts is None or pd.isna(ts):
            return None
        try:
            if isinstance(ts, (int, float, np.integer, np.floating)):
                return pd.to_datetime(ts, unit="s", utc=True).tz_localize(None)
            timestamp = pd.Timestamp(ts)
            if timestamp.tzinfo is not None:
                return timestamp.tz_convert("UTC").tz_localize(None)
            return timestamp
        except Exception:
            return None

    quote_time = normalize_ts(quote_time)
    if quote_time is None:
        quote_time = pd.Timestamp.now(tz="UTC").tz_localize(None)

    def quote_or_bar(key: str, quote_key: str) -> float:
        value = quote.get(quote_key, np.nan)
        if value is None or pd.isna(value):
            value = bar.get(key, np.nan) if bar is not None else np.nan
        return value

    # Sometimes fetching latest price returns volume = 0. This would mess up th predictions. Fix:
    volume = quote_or_bar("Volume", "last_volume")
    if volume == 0 or float(0):
        last_day = fetch_historical_BTCUSD("1y")
        last_day = last_day.tail(1) # Gather latest data row
        volume = int(last_day["Volume"].iloc[-1])

    return pd.DataFrame([{
        "QuoteTime": quote_time,
        "Close": price,
        "High": quote_or_bar("High", "day_high"),
        "Low": quote_or_bar("Low", "day_low"),
        "Open": quote_or_bar("Open", "open"),
        "Volume": volume,
    }])



