import telebot
from config import BOT_TOKEN, ALLOWED_USER_IDS
from suggest import get_trade_suggestions

# Create bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Remove any existing webhook to prevent conflict with polling
bot.remove_webhook()

@bot.message_handler(commands=['suggest'])
def handle_suggest(message):
    if message.from_user.id in ALLOWED_USER_IDS:
        suggestions = get_trade_suggestions()
        if suggestions:
            for suggestion in suggestions:
                bot.send_message(message.chat.id, suggestion)
        else:
            bot.send_message(message.chat.id, "No good trade setups found at the moment.")
    else:
        bot.send_message(message.chat.id, "Access denied.")

# Start polling
bot.polling(non_stop=True)
