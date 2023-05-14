import sys
import os
import json
import pandas as pd
from binance.spot import Spot
from datetime import datetime

client = Spot(
    api_key="_",
    api_secret="_",
)

results_file = "results.csv"
if os.path.exists(results_file):
    os.remove(results_file)


def calculate_sma(data, window):
    return data.rolling(window=window).mean()


def calculate_ema(data, window):
    return data.ewm(span=window, adjust=False).mean()


def main(starting_balance, fast_ma_period, slow_ma_period, ma_type="sma"):
    symbol = "BTCUSDT"
    interval = "4h"
    limit = 1000
    klines_file = "klines.json.tmp"

    if os.path.exists(klines_file):
        with open(klines_file, "r") as f:
            klines = json.load(f)
    else:
        klines = client.klines(symbol=symbol, interval=interval, limit=limit)
        with open(klines_file, "w") as f:
            json.dump(klines, f)

    balance = starting_balance
    max_balance = starting_balance
    max_drawdown = 0
    num_orders = 0
    in_position = False

    # Prepare data
    df = pd.DataFrame(
        klines,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignored",
        ],
    )
    df["close"] = pd.to_numeric(df["close"])

    # Calculate Moving Averages
    if ma_type == "sma":
        df["fast_ma"] = calculate_sma(df["close"], fast_ma_period)
        df["slow_ma"] = calculate_sma(df["close"], slow_ma_period)
    elif ma_type == "ema":
        df["fast_ma"] = calculate_ema(df["close"], fast_ma_period)
        df["slow_ma"] = calculate_ema(df["close"], slow_ma_period)

    for i in range(1, len(df)):
        if df["fast_ma"].iloc[i] > df["slow_ma"].iloc[i] and not in_position:
            print(f"Buy at {df['close'].iloc[i]}")
            balance -= df["close"].iloc[i]  # Assuming we buy 1 unit
            in_position = True
            num_orders += 1
        elif df["fast_ma"].iloc[i] < df["slow_ma"].iloc[i] and in_position:
            print(f"Sell at {df['close'].iloc[i]}")
            balance += df["close"].iloc[i]  # Assuming we sell 1 unit
            in_position = False
            num_orders += 1
            close_date = datetime.utcfromtimestamp(df["time"].iloc[i] / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            print(f"{close_date} {balance}")
            open(results_file, "a").write(f"{close_date},{balance}\n")
            max_balance = max(max_balance, balance)
            max_drawdown = max(max_drawdown, max_balance - balance)

    print(f"Number of orders made: {num_orders}")
    print(f"Final balance: {balance}")
    print(f"Max Drawdown: {max_drawdown}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        script_name = os.path.basename(__file__)
        print(
            f"Usage: python {script_name} <starting_balance> <fast_ma_period> <slow_ma_period> <ma_type>"
        )
        sys.exit(1)

    starting_balance = float(sys.argv[1])
    fast_ma_period = int(sys.argv[2])
    slow_ma_period = int(sys.argv[3])
    ma_type = str(sys.argv[4])

    main(starting_balance, fast_ma_period, slow_ma_period, ma_type)
