import yfinance as yf
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def index(request):
    return render(request, "Accuracy.html")

def calculate_accuracy(request):
    if request.method == 'POST':
        crypto = request.POST['crypto']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']

        print({'crypto':crypto,'sd':start_date, 'ed':end_date })

        # Step 1: Fetch historical data for the selected cryptocurrency
        data = yf.download(crypto + '-USD', start=start_date, end=end_date)

        # Check if data is empty
        if data.empty:
            return HttpResponse("No data available for the selected dates and cryptocurrency.")

        # Step 2: Calculate Daily Returns
        data['Daily Return'] = data['Adj Close'].pct_change()

        # Step 3: Calculate Gain and Loss
        data['Gain'] = data['Daily Return'].apply(lambda x: max(x, 0))
        data['Loss'] = data['Daily Return'].apply(lambda x: max(-x, 0))

        # Step 4: Calculate Average Gain and Average Loss (14-day rolling)
        data['Avg Gain'] = data['Gain'].rolling(window=14).mean()
        data['Avg Loss'] = data['Loss'].rolling(window=14).mean()

        # Step 5: Calculate Relative Strength (RS)
        data['RS'] = data['Avg Gain'] / data['Avg Loss']

        # Step 6: Calculate Relative Strength Index (RSI)
        data['RSI'] = 100 - (100 / (1 + data['RS']))

        # Reset index
        data.reset_index(inplace=True)

        # Step 7: Create a table with the required data
        result_data = data[['Date', 'Adj Close', 'Gain', 'Loss', 'Avg Gain', 'Avg Loss', 'RS', 'RSI']]

        # Calculate Buy and Sell Signals based on RSI
        buy_signal = (result_data['RSI'] <= 30).astype(int)
        sell_signal = (result_data['RSI'] >= 70).astype(int)

        # Combine buy and sell signals into a single signal column
        result_data['Signal'] = buy_signal - sell_signal

        # Step 8: Calculate Actual Signals (Daily Returns > 0)
        actual_signal = (data['Daily Return'] > 0).astype(int)

        # Step 9: Calculate Correct Signals (Buy and Sell signals both are 1)
        correct_signals = (result_data['Signal'] == actual_signal).astype(int)

        # Step 10: Calculate Accuracy
        accuracy = (correct_signals.sum() / len(result_data)) * 100

        # Prepare data for rendering with correct variable names
        context = {
            'accuracy': accuracy,
            'data': result_data.to_dict(orient='records')
        }

        # Render the results in 'Results.html'
        return render(request, 'Results.html', context)

    return HttpResponse("Invalid Request")
