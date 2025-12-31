import os, pytz
from datetime import datetime, time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, JobQueue
from scripts.technical_analysis import get_market_context
from scripts.risk_manager import get_risk_events

load_dotenv()
WIB = pytz.timezone('Asia/Jakarta')

async def generate_market_report():
    pairs = {"GOLD (XAUUSD)": "GC=F", "EURUSD": "EURUSD=X"}
    response = "🔍 **MARKET STATE REPORT**\n"
    response += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for name, sym in pairs.items():
        ctx = get_market_context(sym)
        if ctx:
            response += f"🏆 **{name}**\n"
            response += f"💵 Price: `{ctx['price']}`\n"
            response += f"📈 Bias H4: **{ctx['bias_h4']}**\n"
            response += f"🔗 Alignment: {ctx['alignment']}\n"
            response += f"🏢 Regime: _{ctx['regime']}_\n"
            response += f"⚡ Volatility: {ctx['vol_status']} (ADX: {ctx['adx']})\n"
            response += "──────────────────\n\n"
        else:
            response += f"❌ **{name}**: Data belum stabil.\n\n"
    return response

# --- 1. AUTOMATION: DAILY BRIEFING (07:00 WIB) ---
async def daily_briefing_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    if chat_id:
        report = await generate_market_report()
        await context.bot.send_message(
            chat_id=chat_id, 
            text=f"🌅 **GOOD MORNING!**\n\n{report}", 
            parse_mode='Markdown'
        )

# --- 2. AUTOMATION: NEWS ALERT (H-15 MENIT) ---
async def news_monitor_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    if not chat_id: return
    events = get_risk_events()
    now = datetime.now(WIB)
    for e in events:
        diff = e['datetime_obj'] - now
        if 840 <= diff.total_seconds() <= 900:
            msg = f"⚠️ **NEWS ALERT: 15 MENIT LAGI!**\n"
            msg += f"━━━━━━━━━━━━━━━━━━\n"
            msg += f"🏆 Event: **{e['event']}**\n"
            msg += f"🕒 Jam: `{e['time']}` WIB\n"
            msg += f"ℹ️ Segera amankan posisi!"
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')

# --- 3. AUTOMATION: WEEKLY REFLECTION (JUMAT 22:00 WIB) ---
async def weekly_reflection_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    if not chat_id: return
    
    report = await generate_market_report()
    
    reflection = "🥂 **WEEKLY MARKET REFLECTION**\n"
    reflection += "━━━━━━━━━━━━━━━━━━\n"
    reflection += "Sesi New York Jumat hampir berakhir. Saatnya menutup terminal dan evaluasi.\n\n"
    reflection += "📊 **Status Akhir Pekan:**\n"
    reflection += report
    reflection += "\n🧠 **Mental Check:**\n"
    reflection += "1. Apakah kamu disiplin dengan plan minggu ini?\n"
    reflection += "2. Apakah ada revenge trade yang dilakukan?\n"
    reflection += "3. Berapa banyak 'noise' yang berhasil kamu abaikan?\n\n"
    reflection += "Selamat beristirahat. Market tidak lari ke mana-mana. Sampai jumpa Senin pagi! 🛌"
    
    await context.bot.send_message(chat_id=chat_id, text=reflection, parse_mode='Markdown')

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    await update.message.reply_text(f"🚀 Bot Aktif! Simpan Chat ID ini di .env kamu:\n\n`{user_id}`", parse_mode='Markdown')

async def cek_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Mengklasifikasi Kondisi Market (Professional Mode)...")
    response = await generate_market_report()
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
        context_msg = "Berita High Impact. Potensi slippage dan spread melebar."
        if e.get('currency') == 'EUR': context_msg = "Berita zona Euro. Berdampak langsung pada volatilitas EURUSD."
        elif "FOMC" in e['event']: context_msg = "Suku bunga USD. Volatilitas ekstrim!"

        response += f"🕒 `{e['time']}` | **{e['currency']}**\n"
        response += f"🏆 **{e['event']}**\n"
        response += f"ℹ️ _{context_msg}_\n"
        response += f"📅 {e['date']}\n"
        response += "──────────────────\n"
    
    response += "\n⚠️ *Trading saat news memiliki risiko tinggi.*"
    await update.message.reply_text(response, parse_mode='Markdown')

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN tidak ditemukan!")
    else:
        app = ApplicationBuilder().token(token).build()
        job_queue = app.job_queue
        job_queue.run_daily(daily_briefing_job, time=time(hour=7, minute=0, tzinfo=WIB))
        job_queue.run_repeating(news_monitor_job, interval=60, first=10)
        job_queue.run_daily(weekly_reflection_job, time=time(hour=22, minute=0, tzinfo=WIB), days=(4,))
        # HANDLERS
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('cek', cek_context))
        app.add_handler(CommandHandler('news', news_command))
        
        print("Bot Market Context & Automation Aktif!")
        app.run_polling()