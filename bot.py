import telebot
from suggest import fetch_mexc_futures
from config import BOT_TOKEN, ALLOWED_USER_IDS

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    if message.from_user.id in ALLOWED_USER_IDS:
        bot.send_message(message.chat.id, "✅ Welcome! Use /suggest to get trade ideas.")
    else:
        bot.send_message(message.chat.id, "🚫 You're not authorized to use this bot.")

@bot.message_handler(commands=['suggest'])
def handle_suggest(message):
    if message.from_user.id not in ALLOWED_USER_IDS:
        bot.send_message(message.chat.id, "🚫 Unauthorized.")
        return

    bot.send_message(message.chat.id, "🔍 Analyzing market, please wait...")

    trades = fetch_mexc_futures()
    if not trades:
        bot.send_message(message.chat.id, "❌ No trade signals found.")
        return

    for t in trades:
        reply = f"""
📉 *{t['side'].upper()} SIGNAL*
📈 *Symbol:* `{t['symbol']}`
💰 *Entry:* `{t['entry']}`
🎯 *TP:* `{t['take_profit']}`
🛑 *SL:* `{t['stop_loss']}`
📊 *RR:* `{t['rr']}x`
📦 *Volume:* `{round(t['volume']/1e6, 2)}M USDT`
📌 *Leverage:* `{t['leverage']}x`
        """
        bot.send_message(message.chat.id, reply.strip(), parse_mode="Markdown")

bot.polling()

