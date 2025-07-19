import logging
from telegram.ext import Updater, CommandHandler
from config import TELEGRAM_TOKEN, ALLOWED_USER_IDS
from suggest import handle_suggest

logging.basicConfig(level=logging.INFO)

def start(update, context):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USER_IDS:
        update.message.reply_text("❌ Unauthorized.")
        return
    update.message.reply_text("✅ Send /suggest to get top MEXC AI-based trade ideas.")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("suggest", handle_suggest))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()