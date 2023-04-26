import ccxt
from datetime import datetime

# Creating an object of the Binance exchange API
exchange = ccxt.binance({
    'apiKey': '_',      # API Binance key
    'secret': '_',  # API Binance Secret key
    'enableRateLimit': True,       # Enable request rate limiting
})

# Obtaining historical candlestick data
symbol = 'BTC/USDT'  # Trading pair symbol
timeframe = '4h'  # Timeframe
limit = 1000  # Number of candles to be obtained


ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

# Converting the list of candles into a more convenient format
candles = []
for candle in ohlcv:
    candles.append({
        'timestamp': candle[0],
        'open': candle[1],
        'high': candle[2],
        'low': candle[3],
        'close': candle[4],
        'volume': candle[5]
    })

# Function for defining a pin bar
def is_pinbar(candle):
    # Defining the size of the candle body
    body_size = abs(candle['open'] - candle['close'])
    # Defining the size of the upper and lower shadows
    upper_shadow_size = candle['high'] - max(candle['open'], candle['close'])
    lower_shadow_size = min(candle['open'], candle['close']) - candle['low']

    # Defining the pin bar conditions
    if body_size <= upper_shadow_size and body_size <= lower_shadow_size:
        if candle['close'] > candle['open'] and upper_shadow_size >= 2 * lower_shadow_size:
            return True  # Bullish pin bar
        elif candle['open'] > candle['close'] and lower_shadow_size >= 2 * upper_shadow_size:
            return True  # Bearish pin bar
    return False

# Finding pin bars in historical data and determining the entry point for buying
entry_points = []
potential_profit = 0  # Potential profit
for i in range(2, len(candles)):
    current_candle = candles[i]
    previous_candle = candles[i-1]
    if is_pinbar(previous_candle) and not is_pinbar(current_candle):
        entry_points.append(current_candle)
        potential_profit += current_candle['close'] - previous_candle['close']

# Entering the deposit amount and trade amount
deposit_amount = float(input("Enter the deposit amount: "))
trade_amount = float(input("Enter the trade amount: "))

# Entering the take profit and stop loss percentage
take_profit_percent = float(input("Enter the take profit percentage: "))
stop_loss_percent = float(input("Enter the stop loss percentage: "))

# Calculating the number of possible trades
num_trades = int(deposit_amount / trade_amount)

# Checking that there are enough potential entry points
if num_trades == 0:
    print("Not enough funds to make trades.")
else:
    print("Potential entry points found: ", len(entry_points))
    print("Number of possible trades: ", num_trades)

    # Determining the actual number of trades, limited by the number of potential entry points
    num_trades = min(num_trades, len(entry_points))
    num_trades = min(num_trades, len(entry_points))
    print("Number of trades that will be made: ", num_trades)

    
# Executing trades
for i in range(num_trades):
    entry_point = entry_points[i]
    entry_price = entry_point['close']  # Entry price - closing price
    stop_loss = entry_price * (1 - stop_loss_percent / 100)  # Stop loss level as a percentage of the entry price
    take_profit = entry_price * (1 + take_profit_percent / 100)  # Take profit level as a percentage of the entry price
    potential_profit_abs = take_profit - entry_price  # Potential profit in absolute values
    potential_loss_abs = entry_price - stop_loss  # Potential loss in absolute values
    actual_result = 0  # Actual result

    # Converting timestamp to datetime object
    timestamp = entry_point['timestamp'] / 1000  # Divide by 1000 since ccxt returns time in milliseconds
    date = datetime.fromtimestamp(timestamp)
    date = datetime.fromtimestamp(timestamp)

    # Displaying complete trade information
    if potential_profit_abs >= 0:
        potential_profit_percent = (potential_profit_abs / trade_amount) * 100  # Potential profit as a percentage of the trade amount
        actual_result = potential_profit_abs  # Actual result - potential profit
        print("Trade №{}: Date: {}, Entry price: {:.2f} USD, Take profit price: {:.2f} USD, Stop loss price: {:.2f} USD, Potential result: {:.2f} USD ({:.2f}%)".format(i+1, date.strftime('%Y-%m-%d %H:%M:%S'), entry_price, take_profit, stop_loss, potential_profit_abs, potential_profit_percent))
    else:
        potential_loss_percent = (potential_loss_abs / trade_amount) * 100  # Potential loss as a percentage of the trade amount
        actual_result = -potential_loss_abs  # Actual result - potential loss
        print("Trade №{}: Date: {}, Entry price: {:.2f} USD, Take profit price: {:.2f} USD, Stop loss price: {:.2f} USD, Potential result: {:.2f} USD ({:.2f}%)".format(i+1, entry_date, entry_price, take_profit, stop_loss, potential_loss_abs, potential_loss_percent))
    # Displaying actual result as a percentage of the trade amount
    actual_result_percent = (actual_result / trade_amount) * 100
    print("Actual result: {:.2f} USD ({:.2f}%)".format(actual_result, actual_result_percent))




print("End of program.")

