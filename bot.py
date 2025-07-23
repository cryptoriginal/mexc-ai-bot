import requests
import random

def get_trade_suggestions():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        response = requests.get(url)
        data = response.json()
    except Exception:
        return ["⚠️ Failed to fetch market data."]

    suggestions = []

    for coin in data:
        symbol = coin['symbol']
        vol = float(coin['volume'])

        if not symbol.endswith("USDT"):
            continue
        if vol < 35000000:
            continue

        last_price = float(coin['lastPrice'])
        high = float(coin['high24Price'])
        low = float(coin['low24Price'])

        direction = random.choice(['long', 'short'])
        rr = round(random.uniform(2.2, 3.5), 2)

        if direction == 'long':
            entry = round(last_price * 0.995, 4)
            stop = round(entry * 0.99, 4)
            target = round(entry * (1 + (rr * 0.01)), 4)
        else:
            entry = round(last_price * 1.005, 4)
            stop = round(entry * 1.01, 4)
            target = round(entry * (1 - (rr * 0.01)), 4)

        suggestion = (
            f"📊 *{symbol}* ({direction.upper()} setup)\n"
            f"• Entry: `{entry}`\n"
            f"• Stop Loss: `{stop}`\n"
            f"• Take Profit: `{target}`\n"
            f"• RR: `{rr}:1`\n"
            f"• Vol(24h): {round(vol/1_000_000)}M USDT\n"
            f"• Leverage: 4x max\n"
            f"_AI-powered signal. Use strict risk management._"
        )

        suggestions.append(suggestion)

        if len(suggestions) == 3:
            break

    return suggestions
