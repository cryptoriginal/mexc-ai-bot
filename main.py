import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os
from mexc_api import get_high_volume_pairs
from analysis import generate_signal

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! I'm your MEXC Scalping Bot. Use /suggest to get trading signals."
    )

async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send trading signals."""
    await update.message.reply_text("Analyzing the market...")
    
    try:
        # Get high volume pairs
        high_volume_pairs = await get_high_volume_pairs(min_volume=40_000_000)
        
        if not high_volume_pairs:
            await update.message.reply_text("No high volume pairs found.")
            return
            
        # Generate signals for each pair
        signals = []
        for pair in high_volume_pairs[:5]:  # Limit to top 5 to avoid rate limits
            signal = await generate_signal(pair)
            if signal:
                signals.append(signal)
        
        if not signals:
            await update.message.reply_text("No valid signals found at this time.")
            return
            
        # Format and send signals
        response = "🔥 Scalping Signals 🔥\n\n"
        for signal in signals:
            response += (
                f"📈 Pair: {signal['symbol']}\n"
                f"🎯 Direction: {signal['direction']}\n"
                f"💰 Entry: {signal['entry']}\n"
                f"🛑 Stop Loss: {signal['stop_loss']} ({signal['sl_pct']}%)\n"
                f"✅ Take Profit 1: {signal['tp1']} ({signal['tp1_pct']}%)\n"
                f"✅ Take Profit 2: {signal['tp2']} ({signal['tp2_pct']}%)\n"
                f"📊 Confidence: {signal['confidence']}/10\n"
                f"📌 Reason: {signal['reason']}\n\n"
            )
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error generating signals: {e}")
        await update.message.reply_text("Error generating signals. Please try again later.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("suggest", suggest))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
