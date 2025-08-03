import requests
import time
import telebot
import pandas as pd
import numpy as np
from datetime import datetime

# ==== CONFIG ====
INTERVAL = "1m"              
API_KEY = "8349640206:AAERCdRyD04bD0vZjPR6dNN0P_3Mz9Yn0Bk"   # Telegram bot token
CHAT_ID = "6072953703"     # Telegram Chat ID

bot = telebot.TeleBot(API_KEY)

# ===== RSI Function =====
def rsi_calculation(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ===== MACD Function =====
def macd_calculation(data):
    exp1 = data['close'].ewm(span=12, adjust=False).mean()
    exp2 = data['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# ===== Get Historical Data =====
def get_binance_data(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        data = requests.get(url, timeout=5).json()
        frame = pd.DataFrame(data, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'trades',
            'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        frame['close'] = frame['close'].astype(float)
        return frame
    except:
        return None

# ===== Get All USDT Pairs =====
def get_all_usdt_pairs():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    data = requests.get(url).json()
    symbols = [s['symbol'] for s in data['symbols'] if s['symbol'].endswith('USDT') and 'UP' not in s['symbol'] and 'DOWN' not in s['symbol']]
    return symbols

# ===== Main Bot Loop =====
def run_bot():
    while True:
        try:
            buy_signals = []
            sell_signals = []
            symbols = get_all_usdt_pairs()

            for symbol in symbols:
                df = get_binance_data(symbol, INTERVAL)
                if df is None or df.empty:
                    continue

                df['RSI'] = rsi_calculation(df)
                df['MACD'], df['Signal'] = macd_calculation(df)

                latest_rsi = df['RSI'].iloc[-1]
                latest_macd = df['MACD'].iloc[-1]
                latest_signal = df['Signal'].iloc[-1]

                if latest_rsi < 30 and latest_macd > latest_signal:
                    buy_signals.append(f"{symbol} (RSI: {latest_rsi:.1f})")
                elif latest_rsi > 70 and latest_macd < latest_signal:
                    sell_signals.append(f"{symbol} (RSI: {latest_rsi:.1f})")

            msg = f"📊 SIGNAL UPDATE ({datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC)\n\n"
            if buy_signals:
                msg += "✅ BUY Signals:\n" + "\n".join(buy_signals) + "\n\n"
            else:
                msg += "✅ BUY Signals:\nNone\n\n"

            if sell_signals:
                msg += "❌ SELL Signals:\n" + "\n".join(sell_signals) + "\n"
            else:
                msg += "❌ SELL Signals:\nNone\n"

            bot.send_message(CHAT_ID, msg)
            time.sleep(60)

        except Exception as e:
            print("Error:", e)
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
