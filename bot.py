# bot.py
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import TELEGRAM_TOKEN, MIN_VOLUME_USD, MAX_RESULTS
from scanner import scan_and_rank

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trading-scanner-bot")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi — scanner bot online. Use /suggest to get top trade ideas.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/suggest - run quick scan (may take 10-30s)\n/status - show config")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Min volume USD: {MIN_VOLUME_USD}\nMax results: {MAX_RESULTS}")

async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Scanning for best setups... this can take up to 30 seconds.")
    try:
        # scanning is CPU / IO bound; run in executor
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, scan_and_rank)  # default 15m
        if not results:
            await msg.edit_text("No good setups found right now.")
            return
        texts = []
        for r in results:
            s = r['symbol']
            dirn = r['direction'].upper()
            entry = r['entry']
            sl = r['sl']
            tp = r['tp']
            rr = r['rr']
            score = r['score']
            expl = r['explanation']
            t = f"🔹 {s} — {dirn}\nEntry: {entry:.6f}\nSL: {sl:.6f}\nTP: {tp:.6f}\nRR: {rr:.2f}\nScore: {score}\n{expl}"
            texts.append(t)
        out = "\n\n".join(texts)
        await msg.edit_text(out)
    except Exception as e:
        log.exception("Error in /suggest")
        await msg.edit_text(f"Scanner error: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("suggest", suggest))

    log.info("Starting bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
