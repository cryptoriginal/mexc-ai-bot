import random

def handle_suggest(update, context):
    coin = random.choice(["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    direction = random.choice(["Long", "Short"])
    entry = round(random.uniform(100, 1000), 2)
    sl = round(entry * 0.98, 2)
    tp = round(entry * 1.04, 2)
    rr = round((tp - entry) / (entry - sl), 2)

    msg = f"📈 Coin: {coin}\n📊 Direction: {direction}\n📍 Entry: {entry}\n🎯 TP: {tp}\n🛑 SL: {sl}\n⚖️ RR: {rr}:1\nLeverage: Max 4x"
    update.message.reply_text(msg)