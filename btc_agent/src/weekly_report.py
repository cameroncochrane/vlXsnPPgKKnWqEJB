# Builds the body of the weekly portfolio email sent by timer.py (sending itself is handled by send_email in notification.py)

import logging
from datetime import datetime, timedelta, timezone

import sqlalchemy

from src.database.database import cash_table, fetch_table_data, get_engine, portfolio_table, trades_table
from src.price_data import fetch_live_BTCUSD

logger = logging.getLogger(__name__)

REPORT_DAYS = 7 # How far back "this week" reaches


def _money(value: float, signed: bool = False) -> str:
    """Format ``value`` as dollars, with an explicit +/- sign when ``signed`` (used for profit and loss).

    Example:
        >>> _money(-1234.5, signed=True)
        '-$1,234.50'
    """
    sign = "-" if value < 0 else ("+" if signed else "")
    return f"{sign}${abs(value):,.2f}"


def build_weekly_email(engine: sqlalchemy.Engine | None = None) -> str:
    """Return the plain-text weekly email: a portfolio summary, the open positions, and the trades made in the last 7 days.

    Open positions are valued at the live BTC price. If that can't be fetched, the report still goes out using each position's
    last hourly mark from the database, and says so. Trade times are stored in UTC, so the report is in UTC too.

    Example:
        >>> send_email(subject="Weekly BTC Portfolio Update", message=build_weekly_email())
    """
    engine = engine or get_engine()
    positions = fetch_table_data(engine, portfolio_table)
    trades = fetch_table_data(engine, trades_table)
    cash_rows = fetch_table_data(engine, cash_table)
    cash = cash_rows[0]["cash"] if cash_rows else None

    try:
        live_price = float(fetch_live_BTCUSD()["Close"].iloc[0])
    except Exception:
        logger.exception("Couldn't fetch the live price for the weekly email; using the last stored marks.")
        live_price = None

    now = datetime.now(timezone.utc).replace(tzinfo=None) # SQLite returns stored UTC times without a timezone
    week_start = now - timedelta(days=REPORT_DAYS)
    weekly_trades = sorted((trade for trade in trades if trade["date_time"] >= week_start), key=lambda trade: trade["date_time"])

    position_lines = []
    btc_held = open_value = unrealised = 0.0
    for position in positions:
        price = live_price if live_price is not None else position["current_price"]
        value = position["btc_amnt"] * price
        pnl = (price - position["open_price"]) * position["btc_amnt"]
        btc_held += position["btc_amnt"]
        open_value += value
        unrealised += pnl
        position_lines.append(f"{position['position_id']}: {position['btc_amnt']:.8f} BTC, average entry {_money(position['open_price'])}, value {_money(value)}, unrealised P&L {_money(pnl, signed=True)}")

    trade_lines = [f"{trade['date_time']:%d %b %H:%M}  {trade['trade_id']}  {trade['type'].upper()} {trade['btc_amnt']:.8f} BTC at {_money(trade['price'])} = {_money(trade['value'])} ({trade['position_id']}, realised P&L {_money(trade['realized_pnl'], signed=True)})" for trade in weekly_trades]
    realised_all_time = sum(trade["realized_pnl"] for trade in trades)
    realised_this_week = sum(trade["realized_pnl"] for trade in weekly_trades)

    lines = [
        "Weekly BTC Portfolio Update",
        f"{week_start:%d %b %Y} to {now:%d %b %Y} (UTC)",
        "",
        "SUMMARY",
        f"Portfolio value: {_money((cash or 0.0) + open_value)}",
        f"Cash: {_money(cash) if cash is not None else 'Not set'}",
        f"Open BTC: {btc_held:.8f} BTC, worth {_money(open_value)}",
        f"BTC price: {_money(live_price)}" if live_price is not None else "BTC price: unavailable, so positions are valued at their last hourly mark",
        f"Unrealised P&L: {_money(unrealised, signed=True)}",
        f"Realised P&L this week: {_money(realised_this_week, signed=True)}",
        f"Realised P&L all time: {_money(realised_all_time, signed=True)}",
        "",
        f"OPEN POSITIONS ({len(positions)})",
        *(position_lines or ["None"]),
        "",
        f"TRADES THIS WEEK ({len(weekly_trades)})",
        *(trade_lines or ["None"]),
    ]
    return "\n".join(lines)
