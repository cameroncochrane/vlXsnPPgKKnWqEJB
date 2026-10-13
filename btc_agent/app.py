# Front-end.

# Base imports
import streamlit as st

# Custom imports
from src.price_data import fetch_live_BTCUSD, fetch_historical_BTCUSD


def main():

    st.title('Bitcoin Trading Agent')
    st.text('Development Stage')

    # Fetch current price for displaying quotes and historical prices for plotting.
    btc_current = fetch_live_BTCUSD()
    btc_historical = fetch_historical_BTCUSD(period="max")



    


if __name__ == "__main__":
    main()