import requests
import pandas as pd
from datetime import datetime, timedelta
import time

MEXC_API_URL = "https://contract.mexc.com/api/v1/"

async def get_high_volume_pairs(min_volume=40_000_000):
    """Get trading pairs with volume over the specified threshold."""
    try:
        # Get all contract details
        response = requests.get(f"{MEXC_API_URL}contract/detail")
        response.raise_for_status()
        contracts = response.json()["data"]
        
        # Filter for high volume pairs
        high_volume_pairs = [
            contract["symbol"] for contract in contracts 
            if float(contract["volume"]) >= min_volume
        ]
        
        return high_volume_pairs
        
    except Exception as e:
        print(f"Error fetching high volume pairs: {e}")
        return []

async def get_klines(symbol, interval="15m", limit=100):
    """Get kline data for technical analysis."""
    try:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        response = requests.get(f"{MEXC_API_URL}contract/kline", params=params)
        response.raise_for_status()
        
        # Convert to pandas DataFrame
        klines = response.json()["data"]
        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume"
        ])
        
        # Convert types
        df = df.apply(pd.to_numeric)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        
        return df
        
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
        return None
