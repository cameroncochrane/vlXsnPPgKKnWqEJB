# Backend which orchestrates the overall agent. It is run every hour, being invoked according to timer logic in 'timer.py' (this directory)

from src.price_data import fetch_live_BTCUSD
from src.news import fetch_news_articles
from src.agent import run_agent

def main():

    def return_price():
        # Fetch latest price:
        fetch_live_BTCUSD()
        return None

    current_price = return_price()

    def update_potfolio(current_price):
        
        return None

    current_portfolio = update_potfolio(current_price)


    def generate_price_features(current_price):

        return None

    price_features = generate_price_features(current_price)
    news = fetch_news_articles()

    def models_predict(price_features):
        predictions = {}

        return predictions

    predictions = models_predict(price_features)

    def ask_agent_portfolio(context, current_price, current_portfolio, predictions, news):
        run_agent() # Imported from src.agent
        return None


if __name__ == "__main__":
    main()