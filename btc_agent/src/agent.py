# This script contains the LLM and agentic functionality.

# What functionality does the agent have to be able to trade?:
    # - Inspect the current portfolio and trade history (it may have run before and not remember, so it re-orients itself through these tools every run)
    # - Open/update/close positions in trading.db
    # - Record executed trades in trading.db
    # - Send a Telegram notification when a trade is executed

import os
from datetime import datetime, timezone

from agents import Agent, Runner, function_tool, set_default_openai_key

from src.database.database import (
    add_row,
    fetch_table_data,
    get_engine,
    modify_row,
    portfolio_table,
    remove_row,
    trades_table,
    cash_table
)
from src.notification import chat_id, send_telegram_message

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-6-luna"


@function_tool
def get_portfolio() -> list[dict]:
    """Return every open position currently held, as rows from the portfolio table."""
    engine = get_engine()
    return fetch_table_data(engine, portfolio_table)


@function_tool
def get_trade_history() -> list[dict]:
    """Return every trade ever executed, as rows from the trades table."""
    engine = get_engine()
    return fetch_table_data(engine, trades_table)


@function_tool
def open_position(position_id: str, btc_amnt: float, open_price: float, current_price: float, current_value: float, pnl: float) -> str:
    """Open a new BTC position by inserting a row into the portfolio table."""
    engine = get_engine()
    add_row(engine, portfolio_table, {
        "position_id": position_id,
        "btc_amnt": btc_amnt,
        "open_price": open_price,
        "current_price": current_price,
        "current_value": current_value,
        "pnl": pnl,
        "date_time": datetime.now(timezone.utc),
    })
    return "Position opened."


@function_tool
def update_position(position_id: int, btc_amnt: float, current_price: float, current_value: float, pnl: float) -> str:
    """Update an existing position's size and mark-to-market figures."""
    engine = get_engine()
    modify_row(engine, portfolio_table, {
        "position_id": position_id,
        "btc_amnt": btc_amnt,
        "current_price": current_price,
        "current_value": current_value,
        "pnl": pnl,
        "date_time": datetime.now(timezone.utc)
    })
    return f"Position {position_id} updated."


@function_tool
def close_position(position_id: str) -> str:
    """Close a position entirely by removing it from the portfolio table."""
    engine = get_engine()
    remove_row(engine, portfolio_table, {"position_id": position_id})
    return f"Position {position_id} closed."


@function_tool
def record_trade(trade_type: str, position_id: str, trade_id: str, btc_amnt: float, price: float, value: float, realized_pnl: float) -> str:
    """Record an executed trade (e.g. 'buy' or 'sell') as a row in the trades table."""
    engine = get_engine()
    add_row(engine, trades_table, {
        "type": trade_type,
        "position_id": position_id,
        "trade_id": trade_id,
        "date_time": datetime.now(timezone.utc),
        "btc_amnt": btc_amnt,
        "price": price,
        "value": value,
        "realized_pnl": realized_pnl,
    })
    return "Trade recorded."

@function_tool
def update_cash(cash: float) -> str:
    """ Update the amount of cash present after a trade has been executed"""
    engine = get_engine()
    modify_row(engine, cash_table, {
            "cash": cash,
            "date_time": datetime.now(timezone.utc)
        })
    

@function_tool
def send_trade_notification(message: str) -> str:
    """Send a Telegram message, e.g. to report a trade that was just executed."""
    send_telegram_message(chat_id, message)
    return "Notification sent."


AGENT_INSTRUCTIONS = """
You are an autonomous BTC portfolio-management agent. You are invoked roughly once an hour and
have no memory of previous runs other than what is stored in the database, so always start by
calling get_portfolio and get_trade_history to see what positions you are already holding and
what you have done before.

Given the latest price, recent price history, model predictions, and news context supplied in
the prompt, decide whether to open a new position, adjust or close an existing one, or do
nothing this cycle. Use open_position, update_position, close_position, and record_trade to make
any change durable. Whenever a trade actually executes, call send_trade_notification with a short
human-readable summary of what you did and why.

Finish by returning a brief summary of your decision and reasoning.

Some additional caveats:
- Make sure when opening a position a consistent position_id naming schema is used e.g. P_x (make sure it is unique). The first ever position will 
likely be P_1. Look at the trade history and positions table to understand what positions are open/closed, and the ids associated with them. It is likely that a position
(open or closed) could have multiple trades (T_x) associated with it. Each trade should have unique id and each position should too. Again, refer to trade history to understand
what ids have been used before.

- Don't hallucinate the current price. Use the BTC price provided explicitly to you.

- When you receive historical data it will be for the last 60 days. Feel free to use this data to calculate indicators such as MACD and EMA to help you with your decision.


- Portfolio value can be calculated by considering position values and the cash present (in the cash table).


- Update the cash table after trades have been executed.

"""


def _format_context(context: dict | None) -> str:
    """Render the price/news/prediction context gathered in main.py into a prompt the agent can read."""
    context = context or {}
    sections = []

    current_price = context.get("current_price")
    if current_price is not None and not current_price.empty:
        sections.append(f"Latest BTC-USD quote:\n{current_price.iloc[0].to_dict()}")

    historical_price = context.get("historical_price")
    if historical_price is not None and not historical_price.empty:
        start_close = historical_price["Close"].iloc[0]
        end_close = historical_price["Close"].iloc[-1]
        pct_change = (end_close - start_close) / start_close * 100
        sections.append(
            "Historical price summary:\n"
            f"start_close={start_close:.2f}, end_close={end_close:.2f}, "
            f"min_close={historical_price['Close'].min():.2f}, "
            f"max_close={historical_price['Close'].max():.2f}, "
            f"pct_change={pct_change:.2f}%"
        )

    predictions = context.get("predictions")
    if predictions:
        sections.append(f"Model predictions:\n{predictions}")

    news = context.get("news")
    if news:
        headlines = "\n".join(f"- {article.get('title', 'No title')}" for article in news[:5])
        sections.append(f"Recent news headlines:\n{headlines}")

    current_portfolio = context.get("current_portfolio")
    if current_portfolio:
        sections.append(f"Portfolio snapshot passed in from main.py:\n{current_portfolio}")

    return "\n\n".join(sections) if sections else "No market context was supplied this run."


def run_agent(api_token: str | None = None, context: dict | None = None) -> str:
    """Run the trading agent for one cycle and return its final summary.

    The agent re-orients itself every call via the get_portfolio/get_trade_history tools, then
    uses the price/news/prediction context passed in `context` to decide whether to trade.

    Example:
        >>> run_agent(context={"current_price": current_price, "news": news})
    """
    token = api_token or OPENAI_API_KEY
    if not token:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    set_default_openai_key(token)

    agent = Agent(
        name="BTC Portfolio Agent",
        instructions=AGENT_INSTRUCTIONS,
        model=MODEL,
        tools=[
            get_portfolio,
            get_trade_history,
            open_position,
            update_position,
            close_position,
            record_trade,
            send_trade_notification,
            update_cash
        ],
    )

    result = Runner.run_sync(agent, _format_context(context))
    return result.final_output
