import os, pytz
import time as t_module
from datetime import datetime, time, timedelta
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton, BotCommand
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    JobQueue, CallbackQueryHandler, MessageHandler, filters, Application
)
from telegram.request import HTTPXRequest
from scripts.technical_analysis import get_market_context
from scripts.risk_manager import get_risk_events

load_dotenv()
WIB = pytz.timezone('Asia/Jakarta')

# --- 1. LOGIKA STRATEGI (MENGIKUTI SARAN IDEAL) ---
def get_session_name():
    """Menentukan sesi market berdasarkan jam WIB saat ini."""
    hour = datetime.now(WIB).hour
    if 7 <= hour < 14: return "Asia"
    elif 14 <= hour < 21: return "London"
    else: return "New York"

def derive_action(ctx):
    """Logika Rekomendasi Aksi."""
    regime = ctx.get('regime', '').upper()
    bias = ctx.get('bias_h4', '').upper()
    vol_status = ctx.get('vol_status', '').upper()
    
    if "EXHAUSTED" in vol_status:
        return "❌ WAIT / NO ENTRY (Market Jenuh)"
    
    if "EXPANSION" in regime:
        if "BULLISH" in bias: return "✅ BUY ONLY (Trending Up)"
        if "BEARISH" in bias: return "✅ SELL ONLY (Trending Down)"
    
    if "TRANSITION" in regime:
        return "🔄 SCALPING OK (Mainkan Range)"
        
    return "👀 MONITOR ONLY (Neutral)"

# --- 2. SERVER HEALTH CHECK (HUGGING FACE/RENDER) ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "Bot is alive and monitoring market!"

def run_flask():
    port = int(os.environ.get('PORT', 7860))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- 3. STATE TRACKING ---
last_market_states = {} 
last_prices = {}        
focus_mode = "NORMAL"   

# --- 4. SETTING TOMBOL MENU POJOK KIRI ---
async def post_init(application: Application):
    commands = [
        BotCommand("start", "Mulai/Restart Bot"),
        BotCommand("cek", "Analisis Market Saat Ini"),
        BotCommand("news", "Jadwal Berita High Impact"),
    ]
    await application.bot.set_my_commands(commands)

# --- 5. FUNGSI GENERATE REPORT (VERSI WARAS/IDEAL) ---
async def generate_market_report():
    pairs = {"GOLD (XAUUSD)": "GC=F", "EURUSD": "EURUSD=X"}
    session = get_session_name()
    
    response = "<b>🔍 MARKET STRATEGY REPORT</b>\n"
    response += f"🕒 Session: <b>{session}</b>\n"
    response += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for name, sym in pairs.items():
        ctx = get_market_context(sym)
        if ctx:
            action = derive_action(ctx) # Ambil rekomendasi aksi
            response += f"🏆 <b>{name}</b>\n"
            response += f"Regime      : {ctx['regime']}\n"
            response += f"Volatility  : {ctx['vol_status']}\n"
            response += f"Bias        : {ctx['bias_h4']}\n"
            response += f"Session     : {session}\n"
            response += f"Price       : <code>{ctx['price']}</code>\n\n"
            response += f"🎯 <b>Action:</b>\n<code>{action}</code>\n"
            response += "──────────────────\n\n"
        else:
            response += f"❌ <b>{name}</b>: Data belum stabil.\n\n"
    return response

# --- 6. FUNGSI NEWS COMMAND ---
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message if update.message else update.callback_query.message
    events = get_risk_events()
    if not events:
        await target.reply_text("📭 Tidak ada berita High Impact terdeteksi.", parse_mode='HTML')
        return

    response = "<b>🗓 TRADING PLAN & NEWS CONTEXT</b>\n"
    response += "━━━━━━━━━━━━━━━━━━\n\n"
    for e in events:
        response += f"🕒 <code>{e['time']}</code> | <b>{e['currency']}</b>\n"
        response += f"🏆 <b>{e['event']}</b>\n"
        response += f"📅 {e['date']}\n"
        response += "──────────────────\n"
    
    response += "\n⚠️ <i>Trading saat news memiliki risiko tinggi.</i>"
    await target.reply_text(response, parse_mode='HTML')

# --- 7. MENU KEYBOARD LAYOUT ---
def get_main_menu():
    keyboard = [
        [KeyboardButton("🔍 Cek Market"), KeyboardButton("📅 Jadwal News")],
        [KeyboardButton("🎯 Focus Mode"), KeyboardButton("🔔 Normal Mode"), KeyboardButton("🔕 Silent Mode")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- 8. AUTOMATION JOBS (FULL PACK) ---
async def news_monitor_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    events = get_risk_events()
    now = datetime.now(WIB)
    for e in events:
        diff = (e['datetime_obj'] - now).total_seconds()
        if 840 <= diff <= 900:
            msg = f"⚠️ <b>NEWS ALERT: 15 MENIT LAGI!</b>\n\n🏆 Event: <b>{e['event']}</b>"
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')

async def daily_briefing_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    if chat_id:
        report = await generate_market_report()
        await context.bot.send_message(chat_id=chat_id, text=f"🌅 <b>MORNING BRIEFING</b>\n\n{report}", parse_mode='HTML')

async def session_alert_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    if not chat_id or focus_mode == "SILENT": return
    h = datetime.now(WIB).hour
    msg = ""
    if h == 15: msg = "🚀 <b>LONDON SESSION OPEN</b>\nPerhatikan Liquidity Grab Asia!"
    elif h == 20: msg = "🇺🇸 <b>NEW YORK SESSION OPEN</b>\nHigh Volatility Expected!"
    if msg: await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')

async def intelligence_monitor_job(context: ContextTypes.DEFAULT_TYPE):
    global last_prices
    chat_id = os.getenv("YOUR_CHAT_ID")
    if not chat_id or focus_mode == "SILENT": return
    pairs = {"GOLD": "GC=F", "EURUSD": "EURUSD=X"}
    for name, sym in pairs.items():
        ctx = get_market_context(sym)
        if not ctx: continue
        curr_price = float(ctx['price'])
        if name in last_prices:
            diff = abs(curr_price - last_prices[name])
            if diff > (5.0 if name == "GOLD" else 0.0050):
                # Spike Alert Versi Waras
                msg = f"🚨 <b>SPIKE ALERT</b>\n"
                msg += f"Instrument : <b>{name}</b>\n"
                msg += f"Magnitude  : <code>{diff:.2f}</code>\n"
                msg += f"Status     : <b>HIGH RISK</b>\n\n"
                msg += f"🎯 <b>Action:</b>\n<code>WAIT / NO ENTRY (Volatile)</code>"
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')
        last_prices[name] = curr_price

# --- 9. HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🚀 <b>Bot Forex Alpha Strategis Aktif!</b>",
        reply_markup=get_main_menu(),
        parse_mode='HTML'
    )

async def handle_menu_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔍 Cek Market": await cek_context(update, context)
    elif text == "📅 Jadwal News": await news_command(update, context)
    elif "Mode" in text:
        global focus_mode
        focus_mode = text.split()[0].upper()
        await update.message.reply_text(f"🎯 Mode: <b>{focus_mode}</b>", parse_mode='HTML')

async def cek_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔄 Refresh Harga", callback_data='refresh_harga')],
                [InlineKeyboardButton("📅 Cek News", callback_data='cek_news')]]
    response = await generate_market_report()
    target = update.message if update.message else update.callback_query.message
    await target.reply_text(response, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'refresh_harga':
        response = await generate_market_report()
        await query.edit_message_text(response, parse_mode='HTML', 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh Harga", callback_data='refresh_harga')],
                                              [InlineKeyboardButton("📅 Cek News", callback_data='cek_news')]]))
    elif query.data == 'cek_news': await news_command(update, context)

# --- 10. MAIN EXECUTION ---
if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    if token:
        # Menambah kestabilan jaringan dengan timeout
        t_req = HTTPXRequest(connect_timeout=30, read_timeout=30)
        app = ApplicationBuilder().token(token).request(t_req).post_init(post_init).build()
        
        jq = app.job_queue
        jq.run_daily(daily_briefing_job, time=time(hour=7, minute=0, tzinfo=WIB))
        jq.run_repeating(news_monitor_job, interval=60)
        jq.run_repeating(intelligence_monitor_job, interval=60)
        jq.run_daily(session_alert_job, time=time(hour=15, minute=0, tzinfo=WIB))
        jq.run_daily(session_alert_job, time=time(hour=20, minute=0, tzinfo=WIB))

        app.add_handler(CommandHandler('start', start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu_clicks))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(CommandHandler('cek', cek_context))
        app.add_handler(CommandHandler('news', news_command))
        
        print("🔥 Bot Mode Strategis (200+ Lines) Aktif!")
        keep_alive()
        app.run_polling(bootstrap_retries=-1)