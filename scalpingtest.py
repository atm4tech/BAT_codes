import sys
import os
import json
import arrow
import pandas as pd
import numpy as np
from binance.spot import Spot
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

client = Spot(
    api_key="_",
    api_secret="_",
)

KLINES_MAX_LIMIT = 1000
results_file = "results.csv"
if os.path.exists(results_file):
    os.remove(results_file)


def calculate_SMA(data, window):
    return data.rolling(window=window).mean()


def save_data_to_csv(df, filename):
    df.to_csv(filename, index=False)


def get_latest_klines(symbol, interval, months):
    fromDate = int(arrow.utcnow().shift(months=-months).timestamp() * 1000)
    toDate = int(arrow.utcnow().timestamp() * 1000)

    # estimated_minutes = (toDate - fromDate) / 1000 / 60

    allResults = []
    latestResult = []

    while True:
        latestResult = client.klines(
            symbol=symbol,
            interval=interval,
            startTime=latestResult[-1][6] if len(latestResult) else fromDate,
            limit=KLINES_MAX_LIMIT,
        )
        allResults += latestResult
        # print(f"{(len(allResults) / estimated_minutes) * 100:.1f}% loaded")

        if len(latestResult) < KLINES_MAX_LIMIT:
            break

    return allResults


def main(starting_balance, order_balance_factor, take_profit_factor, stop_loss_factor):
    symbol = "BTCUSDT"
    interval = "5m"
    months = 6
    short_window = 10
    long_window = 50
    klines_file = f"{symbol}_{interval}_klines.json.tmp"

    if os.path.exists(klines_file):
        with open(klines_file, "r") as f:
            klines = json.load(f)
    else:
        klines = get_latest_klines(symbol, interval, months)
        with open(klines_file, "w") as f:
            json.dump(klines, f)

    balance = starting_balance
    max_drawdown = 0
    num_orders = 0
    open_order = None

    data = pd.DataFrame(
        klines,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ],
    )
    data["close"] = data["close"].astype(float)
    data["short_SMA"] = calculate_SMA(data["close"], short_window)
    data["long_SMA"] = calculate_SMA(data["close"], long_window)
    data["signal"] = np.where(data["short_SMA"] > data["long_SMA"], 1.0, 0.0)

    print(f"length={len(data)}")

    for i in range(1, len(data)):
        prev_signal = data["signal"].iloc[i - 1]
        curr_signal = data["signal"].iloc[i]

        # can open order?
        if open_order is None and prev_signal == 0.0 and curr_signal == 1.0:
            close_price = float(data["close"].iloc[i])
            order_size = order_balance_factor * balance
            take_profit_price = close_price * (1 + take_profit_factor)
            stop_loss_price = close_price * (1 - stop_loss_factor)

            open_order = {
                "size": order_size,
                "take_profit": take_profit_price,
                "stop_loss": stop_loss_price,
                "trigger_price": close_price,
                "trigger_time": data["timestamp"].iloc[i],
            }
            num_orders += 1

        # can close order?
        elif open_order is not None:
            high_price = float(data["high"].iloc[i])
            low_price = float(data["low"].iloc[i])
            close_time = data["timestamp"].iloc[i]
            trigger_price = open_order["trigger_price"]

            if high_price >= open_order["take_profit"]:
                balance += open_order["size"] * take_profit_factor
                close_date = datetime.utcfromtimestamp(close_time / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                close_price = open_order["take_profit"]
                print(f"🟢 Profit taken at {close_date}, open price: {trigger_price}")
                open(results_file, "a").write(
                    f"{close_date},{trigger_price},{close_price},{balance}\n"
                )
                open_order = None
            elif low_price <= open_order["stop_loss"]:
                balance -= open_order["size"] * stop_loss_factor
                close_date = datetime.utcfromtimestamp(close_time / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                close_price = open_order["stop_loss"]
                print(f"🔴 Loss stopped at {close_date}, open price: {trigger_price}")
                open(results_file, "a").write(
                    f"{close_date},{trigger_price},{close_price},{balance}\n"
                )
                open_order = None

        drawdown = 1 - balance / starting_balance
        max_drawdown = max(max_drawdown, drawdown)

    percent_increase = ((balance - starting_balance) / starting_balance) * 100

    print(f"Number of orders made: {num_orders}")
    print(f"Resulting balance: {balance:.2f} USDT")
    print(f"Max drawdown: {max_drawdown * 100:.2f}%")
    print(f"Balance increase: {percent_increase:.2f}%")



if __name__ == "__main__":
    if len(sys.argv) != 5:
        script_name = os.path.basename(__file__)
        print(
            f"Usage: python {script_name} <starting_balance> <order_balance_factor> <take_profit_factor> <stop_loss_factor>"
        )
        sys.exit(1)

    starting_balance = float(sys.argv[1])
    order_balance_factor = float(sys.argv[2])
    take_profit_factor = float(sys.argv[3])
    stop_loss_factor = float(sys.argv[4])

    main(
        starting_balance,
        order_balance_factor * 0.01,
        take_profit_factor * 0.01,
        stop_loss_factor * 0.01,
    )
