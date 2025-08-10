import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("8060081170:AAGL3GZsRBhyFUuEQf1PYP-8azEnr3v_2sQ")
    
    # Trading parameters
    MIN_VOLUME = 40_000_000  # 40M minimum volume
    RISK_REWARD_RATIO = 1.5  # Minimum reward:risk ratio
    MAX_SL_PCT = 2.0  # Maximum stop loss percentage
