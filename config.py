# config.py - fill your secrets and basic settings here

# TELEGRAM BOT
TELEGRAM_TOKEN = "REPLACE_WITH_YOUR_TELEGRAM_BOT_TOKEN"

# EXCHANGE: using CCXT exchange id (e.g., "mexc", "binance")
# For MEXC, in CCXT it's typically "mexc" or "mexc3" depending on CCXT version; try "mexc".
EXCHANGE_ID = "mexc"   # change to your exchange if needed

# If you want public-only scanner (no API keys needed) leave API keys blank.
EXCHANGE_API_KEY = ""
EXCHANGE_API_SECRET = ""
EXCHANGE_PASSWORD = ""  # some exchanges require passphrase (usually blank)

# Scanner settings
MIN_VOLUME_USD = 40_000_000  # 40M
MAX_RESULTS = 3              # how many top suggestions to return
MIN_RR = 2.2                 # min required risk:reward
ATR_PERIOD = 14
EMA_FAST = 7
EMA_SLOW = 30

# Optional: use USDT-margined futures market suffix filtering if exchange gives multiple markets
# For mexc example pair naming might be "BTC/USDT:USDT" or symbol.type - you may need to adapt
FUTURES_MARKET_TYPE = "linear"  # just a hint; scanner tries to detect fapi/contract symbols

# Logging / behavior
USE_TESTNET = False  # not used for placing trades (scanner only)
