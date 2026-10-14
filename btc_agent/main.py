# Backend which orchestrates the overall agent. It is run every hour, being invoked according to timer logic in 'timer.py' (this directory)

from src.price_data import fetch_live_BTCUSD
from src.news import fetch_news_articles
from src.agent import run_agent
from src.database.database import create_database, modify_row, fetch_table_data, portfolio_table, trades_table

def main():

    def return_price():
        # Fetch latest price:
        fetch_live_BTCUSD()
        return None

    current_price = return_price()

    def update_potfolio(current_price):
        """
        Make sure any price changes are reflected in the current portfolio. Use the modify_row / fetch_table_data functions from database.py
        """
        
        return None

    current_portfolio = update_potfolio(current_price)


    def generate_price_features(current_price):
        """
        Generate the features required for the ML models to make predictions from the current price
        """
        return None

    price_features = generate_price_features(current_price)
    news = fetch_news_articles() # Fetch the latest news articles for the LLM to use

    def models_predict(price_features):
        """
        Make predictions using the trained ML models and output them for the LLM to use.
        """
        predictions = {}

        return predictions

    predictions = models_predict(price_features)

    def ask_agent_portfolio(current_price, current_portfolio, predictions, news):
        """
        Run the agent by providing all the information it needs to make decisions regarding portfolio management.
        """
        context = {}
        run_agent(api_token=None, context=context) # Imported from src.agent
        return None

    ask_agent_portfolio(current_price, current_portfolio, predictions, news)



if __name__ == "__main__":
    main()