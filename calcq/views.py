import yfinance as yf
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, timedelta

def index(request):
    return render(request, "Accuracy.html")

def calculate_accuracy(request):
    if request.method == 'POST':
        crypto = request.POST['crypto']
        start_date_str = request.POST['start_date']
        end_date_str = request.POST['end_date']
        # Convert start_date and end_date strings to datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
               
        adjusted_start_date = start_date - timedelta(days=13)
        adjusted_end_date = end_date + timedelta(days=1)

                # Fetch the data from Yahoo Finance
        data = yf.download(crypto, start=adjusted_start_date, end=adjusted_end_date)

        

        # Step 1: Fetch historical data for the selected cryptocurrency
        data = yf.download("BTC-USD", start=adjusted_start_date, end=adjusted_end_date)

        # Check if data is empty or not enough data for calculations
        if data.empty or len(data) < 14:
            return HttpResponse("No or insufficient data available for the selected dates and cryptocurrency.")

        # Step 2: Calculate daily price change ('Close' - 'Open')
        data['Price Change'] = data['Close'] - data['Open']


        # Step 3: Split the daily price changes into gains and losses
        data['Gain'] = data['Price Change'].apply(lambda x: max(x, 0))
        data['Loss'] = data['Price Change'].apply(lambda x: max(-x, 0))


        # Step 4: Calculate Average Gain and Average Loss (14-day rolling)
        data['Avg Gain'] = data['Gain'].rolling(window=14).mean()
        data['Avg Loss'] = data['Loss'].rolling(window=14).mean()

        # Filter out rows with NaN values in Avg Gain and Avg Loss
        data = data.dropna(subset=['Avg Gain', 'Avg Loss'])

        # Step 5: Calculate Relative Strength (RS)
        data['RS'] = data['Avg Gain'] / data['Avg Loss']

        # Step 6: Calculate Relative Strength Index (RSI)
        data['RSI'] = 100 - (100 / (1 + data['RS']))

        # Reset index
        data.reset_index(inplace=True)

        # Step 7: Create a table with the required data (Date, Close, Gain, Loss, Avg Gain, Avg Loss, RS, RSI)
        result_data = data[['Date', 'Close', 'Gain', 'Loss', 'Avg Gain', 'Avg Loss', 'RS', 'RSI']]

        # Initialize variables to store bought and sold prices
        bought_price = None
        sold_price = None

        # Calculate Buy and Sell Signals based on RSI
        result_data['Signal'] = 'Hold'
        result_data.loc[result_data['RSI'] <= 30, 'Signal'] = 'Buy'
        result_data.loc[result_data['RSI'] >= 70, 'Signal'] = 'Sell'
        

        # Calculate "Bought" and "Sold" columns and record prices
        result_data['Bought'] = 0
        result_data['Sold'] = 0
        result_data['Price_Bought'] = None
        result_data['Price_Sold'] = None
        result_data['Gain_Signal'] = None
        result_data['Loss_Signal'] = None
        result_data['Win_Loss'] = None  # Initialize Win/Loss column

        for i, row in result_data.iterrows():
            if row['Signal'] == 'Buy':
                result_data.at[i, 'Bought'] = 1
                result_data.at[i, 'Price_Bought'] = bought_price if bought_price else row['Close']
                bought_price = row['Close']
            elif row['Signal'] == 'Sell':
                result_data.at[i, 'Sold'] = 1
                result_data.at[i, 'Price_Sold'] = sold_price if sold_price else row['Close']
                sold_price = row['Close']

                # Calculate Gain_Signal and Loss_Signal
                if bought_price is not None:
                    gain_signal = row['Close'] - bought_price
                    loss_signal = 0 if gain_signal > 0 else bought_price - row['Close']
                    result_data.at[i, 'Gain_Signal'] = gain_signal
                    result_data.at[i, 'Loss_Signal'] = loss_signal
                    
                    # Calculate Win_Loss based on Gain_Signal
                    if gain_signal > 0:
                        result_data.at[i, 'Win_Loss'] = 1  # Win
                    else:
                        result_data.at[i, 'Win_Loss'] = -1  # Loss

                # Reset bought_price and sold_price
                bought_price = None
                sold_price = None

        # Calculate Win_Loss for Hold signals
        result_data['Win_Loss'].fillna(0, inplace=True)  # Fill NaN values with 0
        for i in range(1, len(result_data)):
            if result_data.at[i - 1, 'Signal'] == 'Hold':
                result_data.at[i, 'Win_Loss'] = 1 if result_data.at[i, 'Close'] >= result_data.at[i - 1, 'Close'] else -1
        # Calculate the total number of Wins and Losses
        win_count = (result_data['Win_Loss'] == 'Win').sum()
        loss_count = (result_data['Win_Loss'] == 'Loss').sum()
        
        # Initialize variables to count consecutive signals
        consecutive_wins = 0
        consecutive_losses = 0

        # Calculate consecutive wins and losses
        for i, row in result_data.iterrows():
            if row['Win_Loss'] == 'Win':
                consecutive_wins += 1
                consecutive_losses = 0  # Reset consecutive_losses
            elif row['Win_Loss'] == 'Loss':
                consecutive_losses += 1
                consecutive_wins = 0  # Reset consecutive_wins

            # Count the results of consecutive wins and losses as 1 and -1 respectively
            if consecutive_wins > 0:
                result_data.at[i, 'Win_Loss'] = 1
            elif consecutive_losses > 0:
                result_data.at[i, 'Win_Loss'] = -1

        # Calculate the total number of Wins (1s) and Losses (-1s)
        win_count = (result_data['Win_Loss'] == 1).sum()
        loss_count = (result_data['Win_Loss'] == -1).sum()

        win_count = (result_data['Win_Loss'] == 1).sum()
        loss_count = (result_data['Win_Loss'] == -1).sum()

        # Prepare data for rendering with correct variable names
        results = result_data.to_dict(orient='records')

        for row in results:
            row["Close"] = row.pop("Close")
            row["Avg_gain"] = row.pop("Avg Gain")
        # Reset index
        result_data.reset_index(drop=True, inplace=True)

        # Step 8: Calculate Actual Signals (Price Change > 0)
        actual_signal = (data['Price Change'] > 0).astype(int)

        # Step 9: Calculate Correct Signals (Buy and Sell signals both are 1)
        correct_buy_signals = ((result_data['Bought'] == 1) & (actual_signal == 1)).astype(int)
        correct_sell_signals = ((result_data['Sold'] == 1) & (actual_signal == 0)).astype(int)
        correct_hold_signals = ((result_data['Signal'] == 'Hold') & (result_data['Win_Loss'] == 1)).astype(int)


        # Step 10: Calculate Accuracy
        accuracy_buy = (correct_buy_signals.sum() / len(result_data[result_data['Signal'] == 'Buy'])) * 100
        accuracy_sell = (correct_sell_signals.sum() / len(result_data[result_data['Signal'] == 'Sell'])) * 100
        accuracy_hold = (correct_hold_signals.sum() / len(result_data[result_data['Signal'] == 'Hold'])) * 100

        # Calculate average accuracy
        average_accuracy_buy = accuracy_buy
        average_accuracy_sell = accuracy_sell
        average_accuracy_hold = accuracy_hold

        # Calculate overall accuracy (including inaccurate signals)
        overall_accuracy = ((correct_buy_signals.sum() + correct_sell_signals.sum() + correct_hold_signals.sum()) /
                            len(result_data)) * 100

        # Prepare data for rendering with correct variable names
        results = result_data.to_dict(orient='records')

        for row in results:
            row["Close"] = row.pop("Close")
            row["Avg_gain"] = row.pop("Avg Gain")

        context = {
            'accuracy_buy': accuracy_buy,
            'accuracy_sell': accuracy_sell,
            'accuracy_hold': accuracy_hold,
            'overall_accuracy': overall_accuracy,
            'average_accuracy': (average_accuracy_buy + average_accuracy_sell + average_accuracy_hold) / 3,
            'win_count': win_count,
            'loss_count': loss_count,
            'data': results,
        }

        # Render the results in 'Results.html'
        return render(request, 'Results.html', context)

    return HttpResponse("Invalid Request")
