# scanner.py
import ccxt
import pandas as pd
import numpy as np
import time
from config import *
from utils import compute_atr, is_bullish_engulfing, is_bearish_engulfing, rr_string, format_price, sanitize_symbol

# Build exchange client via CCXT
def build_exchange():
    ex_class = getattr(ccxt, EXCHANGE_ID)
    kwargs = {}
    if EXCHANGE_API_KEY:
        kwargs.update({
            'apiKey': EXCHANGE_API_KEY,
            'secret': EXCHANGE_API_SECRET,
        })
    exchange = ex_class({'enableRateLimit': True, **kwargs})
    return exchange

def fetch_markets(exchange):
    markets = exchange.load_markets(True)
    return markets

def fetch_24h_tickers(exchange):
    # ccxt unified fetch_tickers if available
    try:
        tickers = exchange.fetch_tickers()
    except Exception:
        # fallback: fetchMarkets and fetchTicker per symbol (slow)
        tickers = {}
        for s in exchange.symbols:
            try:
                tickers[s] = exchange.fetch_ticker(s)
            except Exception:
                continue
    return tickers

def symbol_is_futures(mkt):
    # ccxt market entry has 'future' / 'swap' info in type or contract
    typ = mkt.get('type') or mkt.get('future')
    if mkt.get('contract') is True:
        return True
    if typ in ['future', 'swap', 'futures']:
        return True
    return False

def filter_high_volume_pairs(exchange, min_volume_usd=MIN_VOLUME_USD):
    tickers = fetch_24h_tickers(exchange)
    heavy = []
    for sym, t in tickers.items():
        # ticker fields vary; prefer quoteVolume in USDT or convert via last*volume
        vol = t.get('quoteVolume') or t.get('baseVolume') or 0
        last = t.get('last') or 0
        if vol is None:
            continue
        # estimate quoteVolume if only baseVolume present
        qvol = t.get('quoteVolume')
        if qvol is None and last:
            qvol = float(t.get('baseVolume', 0)) * float(last)
        if qvol is None:
            continue
        try:
            qvol = float(qvol)
        except Exception:
            continue
        if qvol >= min_volume_usd:
            heavy.append((sym, qvol, t))
    # sort desc by volume
    heavy_sorted = sorted(heavy, key=lambda x: x[1], reverse=True)
    return heavy_sorted

def fetch_ohlcv_df(exchange, symbol, timeframe='15m', limit=200):
    # returns pandas DataFrame with columns: timestamp, open, high, low, close, volume
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def score_and_build_signal(exchange, symbol, timeframe='15m'):
    try:
        df = fetch_ohlcv_df(exchange, symbol, timeframe=timeframe, limit=300)
    except Exception as e:
        return None
    if df.empty:
        return None

    atr = compute_atr(df, period=ATR_PERIOD).iloc[-1]
    last_close = float(df['close'].iloc[-1])
    last_open = float(df['open'].iloc[-1])
    ema_fast = df['close'].ewm(span=EMA_FAST).mean().iloc[-1]
    ema_slow = df['close'].ewm(span=EMA_SLOW).mean().iloc[-1]

    # determine basic pattern
    idx = len(df)-1
    bull_engulf = is_bullish_engulfing(df, idx)
    bear_engulf = is_bearish_engulfing(df, idx)

    # set SL based on ATR
    if bull_engulf:
        entry = last_close
        sl = entry - 1.0 * atr
        tp = entry + MIN_RR * (entry - sl)  # ensure >= MIN_RR
        direction = 'long'
    elif bear_engulf:
        entry = last_close
        sl = entry + 1.0 * atr
        tp = entry - MIN_RR * (sl - entry)
        direction = 'short'
    else:
        # breakout candidate: if candle closed above recent high or below recent low
        recent_high = df['high'].rolling(20).max().iloc[-2]
        recent_low = df['low'].rolling(20).min().iloc[-2]
        if last_close > recent_high:
            direction = 'long'
            entry = last_close
            sl = recent_low  # conservative
            tp = entry + MIN_RR * (entry - sl)
        elif last_close < recent_low:
            direction = 'short'
            entry = last_close
            sl = recent_high
            tp = entry - MIN_RR * (sl - entry)
        else:
            return None

    # compute real RR
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    rr = reward / risk if risk > 0 else 0.0
    if rr < MIN_RR:
        # not enough RR
        return None

    # trend filter (EMA)
    trend_ok = (direction == 'long' and ema_fast > ema_slow) or (direction == 'short' and ema_fast < ema_slow)
    score = 0
    score += 1 if trend_ok else 0
    score += 1 if (bull_engulf or bear_engulf) else 0
    # volume confirmation: use last volume spike compared to 20-period avg
    vol = df['volume'].iloc[-1]
    vol_avg = df['volume'][-21:-1].mean() if len(df) > 21 else df['volume'].mean()
    score += 1 if vol_avg and vol > 1.5 * vol_avg else 0

    # simple explanation
    expl = []
    expl.append(f"Dir: {direction}")
    expl.append(f"Entry: {format(entry)}")
    expl.append(f"SL: {format(sl)}")
    expl.append(f"TP: {format(tp)}")
    expl.append(rr_string(entry, sl, tp))
    if bull_engulf:
        expl.append("Bullish engulfing")
    if bear_engulf:
        expl.append("Bearish engulfing")
    if trend_ok:
        expl.append("EMA trend OK")
    expl_text = " • ".join(expl)

    return {
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "rr": rr,
        "score": score,
        "explanation": expl_text,
        "last_close": last_close,
        "volume": float(df['volume'].iloc[-1])
    }

def format(result):
    if result is None:
        return None
    s = result['symbol']
    dirn = result['direction'].upper()
    entry = format_price(result['entry'])
    sl = format_price(result['sl'])
    tp = format_price(result['tp'])
    rr = f"{result['rr']:.2f}"
    score = result['score']
    return f"{s} | {dirn} | Entry: {entry} | SL: {sl} | TP: {tp} | RR: {rr} | Score: {score}\n{result['explanation']}"

def scan_and_rank(timeframe='15m', max_results=MAX_RESULTS):
    exchange = build_exchange()
    heavy = filter_high_volume_pairs(exchange, min_volume_usd=MIN_VOLUME_USD)

    results = []
    # iterate top N heavy pairs
    for sym, vol, ticker in heavy[:120]:  # scan top 120 heavy to find best setups
        # filter for USDT or USD quoted, prefer perp symbols ending with USDT
        if "USDT" not in sym and "USD" not in sym:
            continue
        # skip spot-only markets if you want only futures: inspect market data
        mkt = exchange.markets.get(sym)
        if mkt:
            if not symbol_is_futures(mkt):
                # optional skip - keep only futures if desired
                # continue
                pass
        # try scoring
        try:
            sig = score_and_build_signal(exchange, sym, timeframe=timeframe)
        except Exception:
            sig = None
        if sig:
            results.append(sig)
    # rank by score then RR then volume
    results_sorted = sorted(results, key=lambda r: (r['score'], r['rr'], r['volume']), reverse=True)
    return results_sorted[:max_results]
