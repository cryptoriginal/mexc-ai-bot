import requests
import numpy as np

MIN_VOLUME = 35_000_000
MIN_RR = 2.2

def fetch_mexc_futures():
    url = "https://contract.mexc.com/api/v1/contract/kline"
    symbols_url = "https://contract.mexc.com/api/v1/contract/ticker"
    
    try:
        symbols = requests.get(symbols_url, timeout=10).json().get("data", [])
        selected = [s for s in symbols if float(s['amount24']) >= MIN_VOLUME]
        
        trades = []
        for sym in selected[:50]:
            pair = sym['symbol']
            kline_url = f"{url}?symbol={pair}&interval=5m&limit=50"
            klines = requests.get(kline_url).json().get("data", [])
            if len(klines) < 20:
                continue

            candles = parse_klines(klines)
            signal = detect_signal(candles)
            if not signal:
                continue

            entry = float(klines[-1][4])  # last close
            sl, tp = calculate_sl_tp(entry, signal['side'], candles)
            rr = round(abs((tp - entry) / (entry - sl)), 2)
            
            if rr >= MIN_RR:
                trades.append({
                    "symbol": pair,
                    "entry": round(entry, 4),
                    "stop_loss": round(sl, 4),
                    "take_profit": round(tp, 4),
                    "rr": rr,
                    "volume": float(sym['amount24']),
                    "leverage": 3,
                    "side": signal['side'],
                })
        return sorted(trades, key=lambda x: x['rr'], reverse=True)[:3]
    except Exception as e:
        print("Error fetching data:", e)
        return []

def parse_klines(raw):
    return [{
        "open": float(k[1]),
        "high": float(k[2]),
        "low": float(k[3]),
        "close": float(k[4]),
    } for k in raw]

def detect_signal(candles):
    last = candles[-1]
    prev = candles[-2]

    body = abs(last['close'] - last['open'])
    range_ = last['high'] - last['low']
    upper_shadow = last['high'] - max(last['open'], last['close'])
    lower_shadow = min(last['open'], last['close']) - last['low']

    # Hammer
    if lower_shadow > 2 * body and upper_shadow < 0.3 * body:
        return {"side": "long"}
    # Inverted Hammer or Shooting Star
    elif upper_shadow > 2 * body and lower_shadow < 0.3 * body:
        return {"side": "short"}
    # Bullish Engulfing
    elif prev['close'] < prev['open'] and last['close'] > last['open'] and last['close'] > prev['open'] and last['open'] < prev['close']:
        return {"side": "long"}
    # Bearish Engulfing
    elif prev['close'] > prev['open'] and last['close'] < last['open'] and last['close'] < prev['open'] and last['open'] > prev['close']:
        return {"side": "short"}

    return None

def calculate_sl_tp(entry, side, candles):
    closes = [c['close'] for c in candles[-20:]]
    avg_move = np.std(closes) * 1.5

    if side == "long":
        sl = entry - avg_move
        tp = entry + avg_move * 2.2
    else:
        sl = entry + avg_move
        tp = entry - avg_move * 2.2
    return sl, tp

