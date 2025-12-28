import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from scripts.technical_analysis import get_market_context
from scripts.risk_manager import get_risk_events

load_dotenv()

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
        else:
            response += f"**{name}**: Data tidak tersedia (Market Close).\n\n"
            
    await update.message.reply_text(response, parse_mode='Markdown')

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Menyusun rekomendasi trading & jadwal news...")
    events = get_risk_events()
    
    if not events:
        await update.message.reply_text("📭 Tidak ada berita High Impact terdeteksi.")
        return

    response = "🗓 **TRADING PLAN & NEWS CONTEXT**\n"
    response += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for e in events:
        # Tambahkan sedikit konteks otomatis berdasarkan nama berita
        context_msg = ""
        if e['currency'] == 'EUR':
            context_msg = "Berita zona Euro. Berdampak langsung pada volatilitas EURUSD."
        elif "FOMC" in e['event'] or "Federal Funds Rate" in e['event']:
            context_msg = "Suku bunga USD. Volatilitas ekstrim pada Gold & Pair USD."
        elif "NFP" in e['event'] or "Unemployment" in e['event']:
            context_msg = "Data tenaga kerja. Menentukan kekuatan ekonomi AS."
        elif "CPI" in e['event'] or "Inflation" in e['event']:
            context_msg = "Data inflasi. Sangat krusial untuk arah trend jangka panjang."
        else:
            context_msg = "Berita High Impact. Potensi slippage dan spread melebar."

        response += f"🕒 `{e['time']}` | **{e['currency']}**\n"
        response += f"🏆 **{e['event']}**\n"
        response += f"ℹ️ _{context_msg}_\n"
        response += f"📅 {e['date']}\n"
        response += "──────────────────\n"
    
    # BAGIAN REKOMENDASI (Ini yang kamu butuhkan)
    response += "\n💡 **REKOMENDASI BOT:**\n"
    response += "1. **Pre-News (30 Menit Sebelum):** Close posisi yang floating atau amankan dengan SL Plus. Jangan OP baru!\n"
    response += "2. **At News (0-5 Menit):** Hindari Market Execution. Spread bisa melebar 10-50 pips.\n"
    response += "3. **Post-News (15-30 Menit Setelah):** Tunggu 'Price Action' konfirmasi. Jangan lawan arus (Revenge Trade).\n"
    response += "4. **Pair Fokus:** Perhatikan XAUUSD jika news berkaitan dengan USD.\n"
    
    response += "\n⚠️ *Trading saat news memiliki risiko tinggi.*"
    
    await update.message.reply_text(response, parse_mode='Markdown')

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    
    if not token:
        print("Error: TELEGRAM_TOKEN tidak ditemukan di file .env")
    else:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler('cek', cek_context))
        app.add_handler(CommandHandler('news', news_command))
        print("Bot Market Context Aktif!")
        app.run_polling()