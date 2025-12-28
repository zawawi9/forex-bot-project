import os
import yfinance as yf
import pandas_ta as ta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

load_dotenv()

# --- MODULE 1: TECHNICAL CLASSIFIER ---
def get_market_context(symbol):
    df = yf.download(symbol, interval="4h", period="1mo", progress=False)
    if df.empty or len(df) < 60: return None

    # Indikator sesuai kesimpulan baru
    df['EMA30'] = ta.ema(df['Close'], length=30)
    df['EMA60'] = ta.ema(df['Close'], length=60)
    df['ADX'] = ta.adx(df['High'], df['Low'], df['Close'], length=14)['ADX_14']
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    
    # Logika Klasifikasi (Bukan Prediksi)
    last = df.iloc[-1]
    
    # 1. Directional Bias
    bias = "BULLISH" if last['EMA30'] > last['EMA60'] else "BEARISH"
    
    # 2. Trend Strength (ADX)
    adx_val = last['ADX']
    if adx_val < 20: strength = "WEAK/SIDEWAYS"
    elif 20 <= adx_val < 40: strength = "HEALTHY TREND"
    else: strength = "OVEREXTENDED"
    
    # 3. Market Regime
    regime = "TRENDING" if adx_val > 25 else "RANGING/CHOPPY"

    return {
        "bias": bias,
        "strength": strength,
        "regime": regime,
        "atr": round(last['ATR'], 2)
    }

# --- MODULE 2: RISK MONITOR (Simple Version) ---
# Untuk tahap awal, kita buat list manual atau simulasi scraping
def get_risk_events():
    # Nantinya fungsi ini akan melakukan scraping ke ForexFactory
    return [
        {"event": "NFP (USD)", "time": "20:30 WIB", "impact": "High"},
        {"event": "FOMC Meeting", "time": "02:00 WIB", "impact": "High"}
    ]

# --- MODULE 3: TELEGRAM HANDLERS ---
async def cek_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Mengklasifikasi Kondisi Market...")
    
    pairs = {"GOLD": "GC=F", "EURUSD": "EURUSD=X"}
    response = "🔍 **MARKET STATE REPORT**\n\n"
    
    for name, sym in pairs.items():
        ctx = get_market_context(sym)
        if ctx:
            response += f"**{name}**\n"
            response += f"• Bias: {ctx['bias']}\n"
            response += f"• Strength: {ctx['strength']}\n"
            response += f"• Regime: {ctx['regime']}\n"
            response += f"• ATR: {ctx['atr']}\n\n"
            
    response += "⚠️ **RISK MONITOR**\n"
    for e in get_risk_events():
        response += f"• {e['event']} - {e['time']} ({e['impact']})\n"
        
    await update.message.reply_text(response, parse_mode='Markdown')

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler('cek', cek_context))
    print("Bot Market Context Aktif!")
    app.run_polling()