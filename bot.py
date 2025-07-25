import telebot
import threading
import time
from config import BOT_TOKEN, ALLOWED_USER_IDS
from suggest import suggest_trades

bot = telebot.TeleBot(BOT_TOKEN)
auto_loop = False

def send_trade_suggestions(chat_id):
    trades = suggest_trades()
    if not trades:
        bot.send_message(chat_id, "😓 No good trade setup found.")
        return

    for t in trades:
        msg = f"""
📈 *Symbol:* `{t['symbol']}`
📊 *Side:* `{t['side'].capitalize()}`
💰 *Entry:* `{t['entry']}`
🛑 *SL:* `{t['stop_loss']}`
🎯 *TP:* `{t['take_profit']}`
📐 *RR:* `{t['rr']}x`
📦 *Volume:* `{round(t['volume']/1e6, 2)}M USDT`
📌 *Leverage:* `{t['leverage']}x`
        """
        bot.send_message(chat_id, msg.strip(), parse_mode="Markdown")

def auto_loop_thread(chat_id):
    global auto_loop
    while auto_loop:
        bot.send_message(chat_id, "⏳ Auto scan triggered (every 2 min)...")
        send_trade_suggestions(chat_id)
        time.sleep(120)

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in ALLOWED_USER_IDS:
        bot.send_message(message.chat.id, "✅ Welcome! Send /suggest to get a signal. Use /startloop and /stoploop to auto trade alerts.")
    else:
        bot.send_message(message.chat.id, "🚫 Unauthorized.")

@bot.message_handler(commands=['suggest'])
def manual_suggest(message):
    if message.from_user.id in ALLOWED_USER_IDS:
        bot.send_message(message.chat.id, "🔍 Analyzing market, please wait...")
        send_trade_suggestions(message.chat.id)

@bot.message_handler(commands=['startloop'])
def start_auto(message):
    global auto_loop
    if message.from_user.id in ALLOWED_USER_IDS:
        if not auto_loop:
            auto_loop = True
            bot.send_message(message.chat.id, "🔁 Auto mode activated. You'll get signals every 2 minutes.")
            threading.Thread(target=auto_loop_thread, args=(message.chat.id,), daemon=True).start()
        else:
            bot.send_message(message.chat.id, "⚠️ Already running auto loop.")

@bot.message_handler(commands=['stoploop'])
def stop_auto(message):
    global auto_loop
    if message.from_user.id in ALLOWED_USER_IDS:
        auto_loop = False
        bot.send_message(message.chat.id, "🛑 Auto mode stopped.")

bot.polling()


