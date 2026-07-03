import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, time

# ===== YOUR DETAILS =====
TELEGRAM_TOKEN = "PASTE_YOUR_TOKEN_HERE"
CHAT_ID = "PASTE_YOUR_CHAT_ID_HERE"

stocks = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
    "ICICIBANK.NS", "SBIN.NS", "LT.NS", "ITC.NS"
]

signals_today = {}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def get_data(symbol):
    df = yf.download(symbol, interval="5m", period="5d")
    df.dropna(inplace=True)
    return df


def analyze(symbol):
    global signals_today

    try:
        df = yf.download(symbol, interval="5m", period="5d", progress=False)

        if df is None or df.empty:
            print("No data:", symbol)
            return

        df = df.dropna()
        df["date"] = df.index.date

        dates = df["date"].unique()

        if len(dates) < 2:
            return

        yesterday = dates[-2]
        today = dates[-1]

        ydf = df[df["date"] == yesterday]
        tdf = df[df["date"] == today]

        if len(ydf) < 40 or len(tdf) == 0:
            return

        first_candle_high = float(ydf.iloc[0]["High"])
first_candle_low = float(ydf.iloc[0]["Low"])

y_high = float(ydf["High"].max())
y_low = float(ydf["Low"].min())

bearish = first_candle_high == y_high
bullish = first_candle_low == y_low

        block1 = ydf.iloc[:39]
        block2 = ydf.iloc[39:75]

        lvl1 = (block1["High"].max() + block1["Low"].min() + block1["Close"].iloc[-1]) / 3
        lvl2 = (block2["High"].max() + block2["Low"].min() + block2["Close"].iloc[-1]) / 3

        if symbol not in signals_today:
            signals_today[symbol] = False

        for i in range(len(tdf)):
            row = tdf.iloc[i]

            if signals_today[symbol]:
                break

            if row.name.time() < time(9, 20):
                continue

            price = row["Close"]

            if bearish and price < lvl1 and price < lvl2:
                send_telegram(f"🔴 SELL SIGNAL\n{symbol}\nPrice: {price:.2f}")
                signals_today[symbol] = True
                break

            if bullish and price > lvl1 and price > lvl2:
                send_telegram(f"🟢 BUY SIGNAL\n{symbol}\nPrice: {price:.2f}")
                signals_today[symbol] = True
                break

    except Exception as e:
        print("ERROR in", symbol, e)


import time

def run():
    for s in stocks:
        try:
            analyze(s)
        except Exception as e:
            print("ERROR:", s, e)


if __name__ == "__main__":
    while True:
        run()
        time.sleep(300)
