# utils.py
import math
import numpy as np
import pandas as pd

def rr_string(entry: float, sl: float, tp: float) -> str:
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    rr = reward / risk if risk != 0 else float('inf')
    return f"RR: {rr:.2f} ({reward:.2f}/{risk:.2f})"

def format_price(p: float) -> str:
    if p >= 1:
        return f"{p:,.2f}"
    else:
        # smaller ticks
        return f"{p:.8f}"

def sanitize_symbol(sym: str) -> str:
    # simple sanitizer for display
    return sym.replace(":", "/").replace("USDT", "USDT")

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period, min_periods=1).mean()
    return atr

def is_bullish_engulfing(df: pd.DataFrame, idx: int) -> bool:
    # idx is integer index in df (0..len-1)
    if idx < 1:
        return False
    o1, c1 = df['open'].iat[idx-1], df['close'].iat[idx-1]
    o2, c2 = df['open'].iat[idx], df['close'].iat[idx]
    return (c1 < o1) and (c2 > o2) and (c2 >= o1) and (o2 <= c1)

def is_bearish_engulfing(df: pd.DataFrame, idx: int) -> bool:
    if idx < 1:
        return False
    o1, c1 = df['open'].iat[idx-1], df['close'].iat[idx-1]
    o2, c2 = df['open'].iat[idx], df['close'].iat[idx]
    return (c1 > o1) and (c2 < o2) and (c2 <= o1) and (o2 >= c1)

def detect_support_resistance_levels(series: pd.Series, lookback=20):
    # simple pivot approach: return last pivot highs and lows
    highs = []
    lows = []
    for i in range(lookback, len(series)-lookback):
        window = series[i-lookback:i+lookback+1]
        if series[i] == window.max():
            highs.append((i, series[i]))
        if series[i] == window.min():
            lows.append((i, series[i]))
    return highs, lows
