

import yfinance as yf

# Define the ticker symbol (BTC-USD)
ticker_symbol = 'BTC-USD'

# Fetch historical data for BTC-USD for the past 14 days
data = yf.download(ticker_symbol, period='4d')

# Display the fetched data
print(data)
