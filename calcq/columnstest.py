import yfinance as yf
from django.test import TestCase
# Define the ticker symbol (BTC-USD)
stock_symbol = 'BTC-USD' 

stock_data = yf.Ticker(stock_symbol)
        
        # Get all available columns
columns = stock_data.history(period='1d').columns.tolist()
        
        # Print the columns for debugging purposes
print(f"Columns for {stock_symbol}: {columns}")
        
        # Assert that the ticker 'BTC-USD' has at least one column



# Display the fetched data
print(stock_data)
print()

