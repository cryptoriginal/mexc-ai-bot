import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

MIN_VOLUME = 35_000_000
MIN_RR = 2.2

def fetch_mexc_futures():
    try:
        url = "https://contract.mexc.com/api/v1/contract/ticker"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("data", [])
    except:
        return []

def fetch_ohlcv(symbol):
    try:
        url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=1m&limit=100"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = df.astype(float)
        return df
    except:
        return pd.DataFrame()

def detect_reversal_candle(df):
    last = df.iloc[-1]
    body = abs(last.close - last.open)
    range_total = last.high - last.low

    # Bullish Hammer or Doji
    if (last.close > last.open and last.low <= df.low[-5:-1].min()) and (body < 0.4 * range_total):
        return "bullish"
    # Bearish Engulfing or Shooting Star
    if (last.open > last.close and last.high >= df.high[-5:-1].max()) and (body < 0.4 * range_total):
        return "bearish"
    return None

def get_sr_levels(df):
    recent = df[-30:]
    support = recent.low.min()
    resistance = recent.high.max()
    return support, resistance

def calculate_tp_sl(entry, direction, support, resistance):
    if direction == "long":
        stop_loss = support
        risk = entry - stop_loss
        take_profit = entry + risk * MIN_RR
    else:
        stop_loss = resistance
        risk = stop_loss - entry
        take_profit = entry - risk * MIN_RR

    if risk <= 0:
        return None, None  # invalid
    return round(stop_loss, 4), round(take_profit, 4)

def suggest_trades():
    pairs = fetch_mexc_futures()
    results = []

    for p in pairs:
        vol = float(p['amount24'])
        if vol < MIN_VOLUME:
            continue

        symbol = p['symbol']
        df = fetch_ohlcv(symbol)
        if df.empty or len(df) < 30:
            continue

        direction = detect_reversal_candle(df)
        if direction is None:
            continue

        support, resistance = get_sr_levels(df)
        entry = float(df.close.iloc[-1])
        sl, tp = calculate_tp_sl(entry, direction, support, resistance)

        if sl and tp:
            rr = abs((tp - entry) / (entry - sl)) if direction == "long" else abs((entry - tp) / (sl - entry))
            if rr >= MIN_RR:
                results.append({
                    "symbol": symbol,
                    "entry": entry,
                    "stop_loss": sl,
                    "take_profit": tp,
                    "rr": round(rr, 2),
                    "volume": vol,
                    "leverage": 3,
                    "side": direction
                })

    return sorted(results, key=lambda x: x['rr'], reverse=True)[:3]


