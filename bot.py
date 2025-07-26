import telebot
import threading
import time
from config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
from suggest import get_trade_suggestions

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

looping = False

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use /suggest to get trade signals.\n/startloop to get signals every 2 mins.\n/stoploop to stop.")

@bot.message_handler(commands=['suggest'])
def handle_suggest(message):
    user_id = message.from_user.id
    if user_id not in ALLOWED_USER_IDS:
        bot.reply_to(message, "Access denied.")
        return

    bot.reply_to(message, "Analyzing market... please wait ⏳")
    suggestions = get_trade_suggestions()

    if not suggestions:
        bot.send_message(message.chat.id, "❌ No good trade setup found.")
    else:
        for sug in suggestions:
            bot.send_message(message.chat.id, sug)

def auto_loop(chat_id):
    global looping
    while looping:
        try:
            print("🔁 Running loop...")
            suggestions = get_trade_suggestions()
            if not suggestions:
                bot.send_message(chat_id, "❌ [Auto] No good trade setup found.")
            else:
                for sug in suggestions:
                    bot.send_message(chat_id, f"📈 [Auto] {sug}")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ Error in auto loop: {str(e)}")
        time.sleep(120)  # 2 minutes

@bot.message_handler(commands=['startloop'])
def start_loop(message):
    global looping
    user_id = message.from_user.id
    if user_id not in ALLOWED_USER_IDS:
        bot.reply_to(message, "Access denied.")
        return

    if not looping:
        looping = True
        bot.reply_to(message, "✅ Started auto-suggest loop every 2 minutes.")
        thread = threading.Thread(target=auto_loop, args=(message.chat.id,))
        thread.start()
    else:
        bot.reply_to(message, "Loop is already running.")

@bot.message_handler(commands=['stoploop'])
def stop_loop(message):
    global looping
    user_id = message.from_user.id
    if user_id not in ALLOWED_USER_IDS:
        bot.reply_to(message, "Access denied.")
        return

    looping = False
    bot.reply_to(message, "🛑 Stopped auto-suggest loop.")

bot.polling(non_stop=True)


