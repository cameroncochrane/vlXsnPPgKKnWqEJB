# Backend which orchestrates the overall agent. It is run every hour, being invoked according to timer logic in 'timer.py' (this directory)

from src.price_data import fetch_live_BTCUSD

def main():

    def return_price():
        # Fetch latest price:
        fetch_live_BTCUSD()
        return None

    current_price = return_price()

    def update_potfolio(current_price):
        
        return None

    current_portfolio = update_potfolio(current_price)

    def ask_agent_portfolio(current_portfolio):

        return None


    def models_predict():

        return None


if __name__ == "__main__":
    main()