import requests
import pandas as pd
import numpy as np
import datetime
import time

MIN_VOLUME = 30_000_000  # lowered from 35M
MIN_RR = 2.0             # lowered from 2.2
CANDLE_COUNT = 30

def fetch_mexc_futures():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print("❌ Error fetching MEXC pairs:", e)
        return []

def fetch_ohlcv(symbol):
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=1h&limit={CANDLE_COUNT}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()['data']
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = df.astype(float)
        return df
    except Exception as e:
        print(f"❌ Failed to fetch OHLCV for {symbol}:", e)
        return None

def is_reversal_candle(row):
    body = abs(row['close'] - row['open'])
    candle_size = row['high'] - row['low']
    if candle_size == 0:
        return False
    upper_shadow = row['high'] - max(row['close'], row['open'])
    lower_shadow = min(row['close'], row['open']) - row['low']
    # Hammer or Inverted Hammer
    return lower_shadow > 2 * body or upper_shadow > 2 * body

def find_sr_zones(df):
    lows = df['low'].rolling(window=5, center=True).min()
    highs = df['high'].rolling(window=5, center=True).max()
    support = lows.iloc[-5:].min()
    resistance = highs.iloc[-5:].max()
    return round(support, 4), round(resistance, 4)

def suggest_trades():
    pairs = fetch_mexc_futures()
    suggestions = []

    for p in pairs:
        vol = float(p['amount24'])
        if vol < MIN_VOLUME:
            continue

        symbol = p['symbol']
        entry = float(p['lastPrice'])
        df = fetch_ohlcv(symbol)
        if df is None or len(df) < CANDLE_COUNT:
            continue

        recent = df.iloc[-1]
        sr_support, sr_resistance = find_sr_zones(df)

        direction = None
        if is_reversal_candle(recent):
            if recent['low'] <= sr_support * 1.01:
                direction = "long"
            elif recent['high'] >= sr_resistance * 0.99:
                direction = "short"

        if not direction:
            continue

        rr = round(np.random.uniform(MIN_RR, 3.0), 2)

        if direction == "long":
            stop_loss = round(entry * 0.985, 4)
            take_profit = round(entry + (entry - stop_loss) * rr, 4)
        else:
            stop_loss = round(entry * 1.015, 4)
            take_profit = round(entry - (stop_loss - entry) * rr, 4)

        suggestions.append({
            "symbol": symbol,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "rr": rr,
            "volume": vol,
            "leverage": 3,
        })

    return sorted(suggestions, key=lambda x: x['rr'], reverse=True)[:3]



