import requests
import random
import numpy as np

# AI filtering rules
MIN_VOLUME = 35_000_000  # 35M USDT 24h volume
MIN_RR = 2.2  # Minimum 1:2.2 risk-reward

def fetch_mexc_futures():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print("Error fetching MEXC pairs:", e)
        return []

def fake_ai_score(pair):
    """
    Placeholder for AI logic.
    Returns a fake risk-reward score based on volume & random logic.
    """
    vol = float(pair['amount24'])
    rr_score = round(random.uniform(MIN_RR, 3.5), 2)
    return rr_score if vol >= MIN_VOLUME else 0

def suggest_trades():
    pairs = fetch_mexc_futures()
    safe_trades = []

    for p in pairs:
        rr = fake_ai_score(p)
        if rr >= MIN_RR:
            entry = float(p['lastPrice'])
            stop_loss = round(entry * 0.985, 4)  # 1.5% SL
            take_profit = round(entry + (entry - stop_loss) * rr, 4)

            safe_trades.append({
                "symbol": p['symbol'],
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "rr": rr,
                "volume": float(p['amount24']),
                "leverage": 3,
            })

    # Sort by RR descending, pick top 1–3
    top = sorted(safe_trades, key=lambda x: x['rr'], reverse=True)[:3]
    return top
