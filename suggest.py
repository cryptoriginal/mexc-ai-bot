import requests

MIN_VOLUME = 35_000_000
MIN_RR = 2.2

def fetch_mexc_futures():
    url = "https://contract.mexc.com/api/v1/contract/kline/1m"
    try:
        tickers = requests.get("https://contract.mexc.com/api/v1/contract/ticker", timeout=10).json().get("data", [])
        pairs = []
        for ticker in tickers:
            if float(ticker['amount24']) < MIN_VOLUME:
                continue
            symbol = ticker['symbol']
            candles = requests.get(f"{url}?symbol={symbol}&limit=30", timeout=10).json().get("data", [])
            if len(candles) < 10:
                continue
            pairs.append({"symbol": symbol, "volume": float(ticker['amount24']), "lastPrice": float(ticker['lastPrice']), "candles": candles})
        return pairs
    except Exception as e:
        print("❌ Error fetching data:", e)
        return []

def detect_reversal(candles):
    last = candles[-2]
    body = abs(float(last[1]) - float(last[4]))
    wick_top = float(last[2]) - max(float(last[1]), float(last[4]))
    wick_bottom = min(float(last[1]), float(last[4])) - float(last[3])

    # Bullish reversal candle (e.g. hammer)
    if wick_bottom > 2 * body and body > 0:
        return 'long'
    # Bearish reversal candle (e.g. inverted hammer / shooting star)
    elif wick_top > 2 * body and body > 0:
        return 'short'
    else:
        return None

def suggest_trades():
    pairs = fetch_mexc_futures()
    results = []

    for p in pairs:
        side = detect_reversal(p['candles'])
        if not side:
            continue

        price = p['lastPrice']
        leverage = 3

        if side == 'long':
            sl = round(price * 0.985, 4)  # 1.5% SL
            tp = round(price + (price - sl) * MIN_RR, 4)
        else:
            sl = round(price * 1.015, 4)  # 1.5% SL above
            tp = round(price - (sl - price) * MIN_RR, 4)

        rr = round(abs(tp - price) / abs(price - sl), 2)
        if rr < MIN_RR:
            continue

        results.append({
            "symbol": p['symbol'],
            "entry": price,
            "stop_loss": sl,
            "take_profit": tp,
            "rr": rr,
            "volume": p['volume'],
            "leverage": leverage,
            "side": side
        })

    return sorted(results, key=lambda x: x['rr'], reverse=True)[:3]

