import requests
import random
import pandas as pd
import numpy as np
import datetime

def fetch_klines(symbol, interval='1m', limit=100):
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def is_bullish_engulfing(prev, curr):
    return prev['close'] < prev['open'] and curr['close'] > curr['open'] and curr['close'] > prev['open'] and curr['open'] < prev['close']

def is_bearish_engulfing(prev, curr):
    return prev['close'] > prev['open'] and curr['close'] < curr['open'] and curr['close'] < prev['open'] and curr['open'] > prev['close']

def detect_reversal(df):
    if len(df) < 5:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if is_bullish_engulfing(prev, last):
        return 'long'
    elif is_bearish_engulfing(prev, last):
        return 'short'
    return None

def find_support_resistance(df):
    recent_lows = df['low'].rolling(window=20).min()
    recent_highs = df['high'].rolling(window=20).max()
    return recent_lows.iloc[-1], recent_highs.iloc[-1]

def get_trade_suggestions():
    url = "https://api.mexc.com/api/v3/ticker/24hr"
    res = requests.get(url).json()
    coins = [coin['symbol'] for coin in res if 'USDT' in coin['symbol'] and not coin['symbol'].endswith('3S') and float(coin['quoteVolume']) > 35000000]

    signals = []
    for symbol in coins[:25]:  # scan only top 25 for speed
        df = fetch_klines(symbol)
        if df is None or len(df) < 30:
            continue

        signal = detect_reversal(df)
        if not signal:
            continue

        support, resistance = find_support_resistance(df)
        current_price = df.iloc[-1]['close']

        if signal == 'long':
            sl = support
            tp = current_price + (current_price - sl) * 2.2
        else:
            sl = resistance
            tp = current_price - (sl - current_price) * 2.2

        rr = abs(tp - current_price) / abs(current_price - sl)
        if rr < 2.2:
            continue

        direction_emoji = "🟢 LONG" if signal == 'long' else "🔴 SHORT"
        signals.append(f"{direction_emoji} {symbol}\nEntry: {round(current_price, 4)}\nSL: {round(sl, 4)}\nTP: {round(tp, 4)}\nRR: {round(rr, 2)}")

    return signals



