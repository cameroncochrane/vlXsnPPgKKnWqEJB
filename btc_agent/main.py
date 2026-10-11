# Backend which orchestrates the overall agent. It is run every hour, being invoked according to timer logic in 'timer.py' (this directory)

from src.price_data import fetch_live_BTCUSD

def main():

    def return_price():
        # Fetch latest price:
        fetch_live_BTCUSD()
        return None

    def check_potfolio():
        
        return None

    def ask_agent_portfolio(portfolio):

        return None


    def models_predict():

        return None


if __name__ == "__main__":
    main()