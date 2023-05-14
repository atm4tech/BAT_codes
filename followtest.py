import sys
import os
import json
from binance.spot import Spot
from datetime import datetime

client = Spot(
    api_key="_",
    api_secret="_",
)

results_file = "results.csv"
if os.path.exists(results_file):
    os.remove(results_file)


def sma(close_prices, period):
    if len(close_prices) < period:
        return None
    return sum(close_prices[-period:]) / period


def follow_the_trend(candle, close_prices, sma_period):
    close_price = float(candle[4])
    close_prices.append(close_price)
    average = sma(close_prices, sma_period)

    if average is None:
        return False
    return close_price > average


def main(starting_balance, order_balance_factor, take_profit_factor, stop_loss_factor):
    symbol = "BTCUSDT"
    interval = "4h"
    limit = 1000
    klines_file = f"{symbol}_{interval}_klines.json.tmp"

    if os.path.exists(klines_file):
        with open(klines_file, "r") as f:
            klines = json.load(f)
    else:
        klines = client.klines(symbol=symbol, interval=interval, limit=limit)
        with open(klines_file, "w") as f:
            json.dump(klines, f)

    balance = starting_balance
    max_drawdown = 0
    num_orders = 0

    open_order = None

    sma_period = 10
    close_prices = []

    for i in range(1, len(klines)):
        prev_candle = klines[i - 1]
        curr_candle = klines[i]

        # can open order?
        if open_order is None and follow_the_trend(
            prev_candle, close_prices, sma_period
        ):
            close_price = float(curr_candle[4])
            order_size = order_balance_factor * balance
            take_profit_price = close_price * (1 + take_profit_factor)
            stop_loss_price = close_price * (1 - stop_loss_factor)

            open_order = {
                "size": order_size,
                "take_profit": take_profit_price,
                "stop_loss": stop_loss_price,
                "trigger_price": close_price,
                "trigger_time": curr_candle[0],
            }
            num_orders += 1

        # can close order?
        elif open_order is not None:
            high_price = float(curr_candle[2])
            low_price = float(curr_candle[3])
            close_time = curr_candle[0]
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
