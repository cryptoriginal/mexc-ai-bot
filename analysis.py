import talib
import numpy as np
from typing import Dict, Optional
from mexc_api import get_klines

async def generate_signal(symbol: str) -> Optional[Dict]:
    """Generate a trading signal for the given symbol."""
    # Get kline data
    df = await get_klines(symbol)
    if df is None or len(df) < 50:  # Need enough data for indicators
        return None
    
    # Calculate indicators
    df = calculate_indicators(df)
    
    # Analyze patterns and generate signal
    signal = analyze_for_signal(df, symbol)
    
    return signal

def calculate_indicators(df):
    """Calculate all technical indicators."""
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    
    # Trend indicators
    df["ema_20"] = talib.EMA(close, timeperiod=20)
    df["ema_50"] = talib.EMA(close, timeperiod=50)
    df["ema_200"] = talib.EMA(close, timeperiod=200)
    
    # Momentum indicators
    df["rsi"] = talib.RSI(close, timeperiod=14)
    df["macd"], df["macd_signal"], _ = talib.MACD(close)
    
    # Volatility
    df["atr"] = talib.ATR(high, low, close, timeperiod=14)
    
    # Support/Resistance
    df["support"], df["resistance"] = find_support_resistance(high, low)
    
    return df

def find_support_resistance(high, low, lookback=20):
    """Identify key support and resistance levels."""
    # Simple implementation - can be enhanced with more sophisticated methods
    support = np.min(low[-lookback:])
    resistance = np.max(high[-lookback:])
    return support, resistance

def analyze_for_signal(df, symbol):
    """Analyze indicators and patterns to generate a signal."""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Initialize signal structure
    signal = {
        "symbol": symbol,
        "direction": None,
        "entry": None,
        "stop_loss": None,
        "sl_pct": None,
        "tp1": None,
        "tp1_pct": None,
        "tp2": None,
        "tp2_pct": None,
        "confidence": 0,
        "reason": []
    }
    
    # Check for trend direction
    trend_up = latest["ema_20"] > latest["ema_50"] > latest["ema_200"]
    trend_down = latest["ema_20"] < latest["ema_50"] < latest["ema_200"]
    
    # Check RSI conditions
    oversold = latest["rsi"] < 30
    overbought = latest["rsi"] > 70
    
    # Check MACD crossover
    macd_bullish = latest["macd"] > latest["macd_signal"] and prev["macd"] < prev["macd_signal"]
    macd_bearish = latest["macd"] < latest["macd_signal"] and prev["macd"] > prev["macd_signal"]
    
    # Check price relative to support/resistance
    near_support = abs(latest["close"] - latest["support"]) / latest["support"] < 0.005
    near_resistance = abs(latest["close"] - latest["resistance"]) / latest["resistance"] < 0.005
    
    # Generate signal logic
    if trend_up and (oversold or macd_bullish) and near_support:
        # Potential long signal
        signal["direction"] = "LONG"
        signal["entry"] = latest["close"]
        signal["stop_loss"] = latest["support"] * 0.995  # Just below support
        signal["sl_pct"] = round((1 - signal["stop_loss"]/signal["entry"]) * 100, 2)
        
        # Set take profits based on ATR
        atr = latest["atr"]
        signal["tp1"] = signal["entry"] + atr * 0.5
        signal["tp1_pct"] = round((signal["tp1"]/signal["entry"] - 1) * 100, 2)
        signal["tp2"] = signal["entry"] + atr * 1.0
        signal["tp2_pct"] = round((signal["tp2"]/signal["entry"] - 1) * 100, 2)
        
        signal["confidence"] = 7  # Medium-high confidence
        signal["reason"].append("Trend is up")
        if oversold:
            signal["reason"].append("RSI indicates oversold")
        if macd_bullish:
            signal["reason"].append("MACD bullish crossover")
        if near_support:
            signal["reason"].append("Price near support level")
            
    elif trend_down and (overbought or macd_bearish) and near_resistance:
        # Potential short signal
        signal["direction"] = "SHORT"
        signal["entry"] = latest["close"]
        signal["stop_loss"] = latest["resistance"] * 1.005  # Just above resistance
        signal["sl_pct"] = round((signal["stop_loss"]/signal["entry"] - 1) * 100, 2)
        
        # Set take profits based on ATR
        atr = latest["atr"]
        signal["tp1"] = signal["entry"] - atr * 0.5
        signal["tp1_pct"] = round((1 - signal["tp1"]/signal["entry"]) * 100, 2)
        signal["tp2"] = signal["entry"] - atr * 1.0
        signal["tp2_pct"] = round((1 - signal["tp2"]/signal["entry"]) * 100, 2)
        
        signal["confidence"] = 7  # Medium-high confidence
        signal["reason"].append("Trend is down")
        if overbought:
            signal["reason"].append("RSI indicates overbought")
        if macd_bearish:
            signal["reason"].append("MACD bearish crossover")
        if near_resistance:
            signal["reason"].append("Price near resistance level")
    
    # Combine reasons
    if signal["reason"]:
        signal["reason"] = ", ".join(signal["reason"])
        return signal
    
    return None
