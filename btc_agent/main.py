# Backend which orchestrates the overall agent. It is run every hour, being invoked according to timer logic in 'timer.py' (this directory)

from datetime import datetime, timezone

import pandas as pd

from src.price_data import fetch_live_BTCUSD, fetch_historical_BTCUSD
from src.price_indicators import add_SMA, add_EMA, add_ranges, add_RSI, add_MACD
from src.news import fetch_news_articles
from src.agent import run_agent
from src.database.database import create_database, modify_row, fetch_table_data, portfolio_table, trades_table
from src.notification import send_email

from src.paths import APP_ROOT

def main():

    def return_price():
        current_price = fetch_live_BTCUSD() # Fetch latest price
        three_month_data = fetch_historical_BTCUSD(period="3mo") # Historical data (for context)
        
        return current_price, three_month_data

    current_price, three_month_data = return_price()

    def add_price_indicators(historical_data):
        """
        Add technical indicators to the daily historical data so the agent can see them (it can't calculate them itself).
        """
        data = add_SMA(data=historical_data, n=7)
        data = add_SMA(data=data, n=20)
        data = add_EMA(data=data, n=7)
        data = add_EMA(data=data, n=20)
        data = add_ranges(data=data)
        data = add_RSI(data=data)
        data = add_MACD(data=data)

        return data

    three_month_data = add_price_indicators(three_month_data)

    def update_portfolio(current_price: pd.DataFrame) -> list[dict[str, object]]:
        """
        Mark every open position to the latest BTC price, so the portfolio table (and the agent) see up-to-date values.

        For each row in the portfolio table this sets current_price to the latest close, current_value to
        btc_amnt * current_price, and pnl (unrealised) to (current_price - open_price) * btc_amnt.
        Returns the updated open positions as dictionaries (an empty list if no positions are open).

        Example:
            >>> current_price = fetch_live_BTCUSD()
            >>> current_portfolio = update_portfolio(current_price)
            >>> current_portfolio[0]["pnl"]
            250.0
        """
        price = float(current_price["Close"].iloc[0])
        updated_at = datetime.now(timezone.utc)
        engine = create_database()

        for position in fetch_table_data(engine, portfolio_table):
            btc_amnt = position["btc_amnt"]
            modify_row(engine, portfolio_table, {"position_id": position["position_id"], "current_price": price, "current_value": btc_amnt * price, "pnl": (price - position["open_price"]) * btc_amnt, "date_time": updated_at})

        return fetch_table_data(engine, portfolio_table)

    current_portfolio = update_portfolio(current_price)


    def generate_price_features(current_price, three_month_data):
        """
        Select the exact columns (in training order) each ML model expects from the indicator data built by add_price_indicators.
        The models were trained on a different column set to the one shown to the agent (e.g. dcn_20_lr_ht expects
        Close, High, Low, Open, Volume, SMA_7, EMA_7, IDR, ATR_4, RSI_14, MACD, MACD_signal, MACD_hist, with no Date, SMA_20 or EMA_20).
        """
        return None

    price_features = generate_price_features(current_price, three_month_data)
    news = fetch_news_articles() # Fetch the latest news articles for the LLM to use

    def models_predict(price_features):
        """
        Make predictions using the trained ML models and output them for the LLM to use.
        """
        ### Use the direction and volatility models here ###
        predictions = {}

        return predictions

    predictions = models_predict(price_features)

    def ask_agent_portfolio(current_price, historical_price, current_portfolio, predictions, news):
        """
        Run the agent by providing all the information it needs to make decisions regarding portfolio management.
        """
        context = {
            "current_price": current_price,
            "historical_price": historical_price,
            "current_portfolio": current_portfolio,
            "predictions": predictions,
            "news": news,
        }
        return run_agent(api_token=None, context=context) # Imported from src.agent

    agent_summary = ask_agent_portfolio(current_price, three_month_data, current_portfolio, predictions, news)
    print(agent_summary)

    
if __name__ == "__main__":
    main()
    