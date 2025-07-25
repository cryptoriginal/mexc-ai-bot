import telebot
from suggest import suggest_trades
from config import BOT_TOKEN, ALLOWED_USER_IDS

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    if message.from_user.id in ALLOWED_USER_IDS:
        bot.send_message(message.chat.id, "✅ Welcome! Use /suggest for trades.")
    else:
        bot.send_message(message.chat.id, "🚫 You're not authorized.")

@bot.message_handler(commands=['suggest'])
def handle_suggest(message):
    if message.from_user.id not in ALLOWED_USER_IDS:
        bot.send_message(message.chat.id, "🚫 Unauthorized.")
        return

    bot.send_message(message.chat.id, "🔍 Analyzing charts...")

    trades = suggest_trades()
    if not trades:
        bot.send_message(message.chat.id, "😓 No valid trade found.")
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

        """
        bot.send_message(message.chat.id, reply.strip(), parse_mode="Markdown")

# Start polling
bot.polling()
