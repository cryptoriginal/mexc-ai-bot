import telebot
import threading
import time
from suggest import suggest_trades
from config import TELEGRAM_BOT_TOKEN

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Global loop control
auto_loop_running = False
loop_thread = None

# Helper to format and send trade signals
def send_trade_suggestions(chat_id):
    bot.send_message(chat_id, "📊 Analyzing market... please wait.")
    suggestions = suggest_trades()
    if not suggestions:
        bot.send_message(chat_id, "😕 No good trade setup found right now.")
        return

    for trade in suggestions:
        msg = (
            f"📈 *Signal:* `{trade['symbol']}`\n"
            f"🔁 Direction: *{'LONG' if trade['take_profit'] > trade['entry'] else 'SHORT'}*\n"
            f"🎯 Entry: `{trade['entry']}`\n"
            f"❌ Stop Loss: `{trade['stop_loss']}`\n"
            f"✅ Take Profit: `{trade['take_profit']}`\n"
            f"⚖️ Risk-Reward: `{trade['rr']}`\n"
            f"⚡ Leverage: `{trade['leverage']}x`\n"
            f"📊 24h Volume: `{int(trade['volume'])}` USDT"
        )
        bot.send_message(chat_id, msg, parse_mode="Markdown")

# Loop thread function
def loop_suggestions(chat_id):
    global auto_loop_running
    while auto_loop_running:
        send_trade_suggestions(chat_id)
        time.sleep(120)  # every 2 minutes

# /suggest command
@bot.message_handler(commands=["suggest"])
def handle_suggest(message):
    send_trade_suggestions(message.chat.id)

# /startloop command
@bot.message_handler(commands=["startloop"])
def handle_startloop(message):
    global auto_loop_running, loop_thread
    if auto_loop_running:
        bot.send_message(message.chat.id, "⚠️ Auto-loop already running.")
        return
    auto_loop_running = True
    loop_thread = threading.Thread(target=loop_suggestions, args=(message.chat.id,))
    loop_thread.start()
    bot.send_message(message.chat.id, "✅ Auto-signal loop started. You’ll get updates every 2 minutes.")

# /stoploop command
@bot.message_handler(commands=["stoploop"])
def handle_stoploop(message):
    global auto_loop_running
    auto_loop_running = False
    bot.send_message(message.chat.id, "🛑 Auto-signal loop stopped.")

# /start command (optional)
@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(message.chat.id, "👋 Welcome! Use /suggest to get trade ideas.\nUse /startloop to receive signals every 2 mins.\nUse /stoploop to stop it.")

print("🤖 Bot is running...")
bot.polling(non_stop=True)

