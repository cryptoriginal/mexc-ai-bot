import telebot
from config import BOT_TOKEN, ALLOWED_USER_IDS
from suggest import get_trade_suggestions

bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()  # Ensures getUpdates works without webhook conflict

@bot.message_handler(commands=['suggest'])
def handle_suggest(message):
    if message.from_user.id in ALLOWED_USER_IDS:
        suggestions = get_trade_suggestions()
        if suggestions:
            for s in suggestions:
                bot.send_message(message.chat.id, s)
        else:
            bot.send_message(message.chat.id, "No good trade setups found at the moment.")
    else:
        bot.send_message(message.chat.id, "Access denied.")

bot.polling(non_stop=True)

        """
        bot.send_message(message.chat.id, reply.strip(), parse_mode="Markdown")

# Start polling
bot.polling()
