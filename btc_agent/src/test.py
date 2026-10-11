from price_data import fetch_historical_BTCUSD, fetch_live_BTCUSD

data = fetch_live_BTCUSD()
print(data.tail())

#data = fetch_historical_BTCUSD("1y")
#last = data.tail(1)
#print(int(last["Volume"].iloc[-1]))