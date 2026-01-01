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

# --- 1. PERFORMANCE & STRATEGY ENGINE ---
def get_session_name():
    """Menentukan sesi market berdasarkan jam WIB."""
    hour = datetime.now(WIB).hour
    if 7 <= hour < 14: return "Asia"
    elif 14 <= hour < 21: return "London"
    else: return "New York"

def calculate_performance(name, current_price, open_price):
    """Kalkulasi Pips (Forex) atau Points (Gold)."""
    change = current_price - open_price
    if "GOLD" in name.upper() or "XAU" in name.upper():
        return f"{change:+.2f} Pts"
    return f"{(change * 10000):+.1f} Pips"

def derive_action(ctx):
    """Logika Rekomendasi Aksi (Versi Waras)."""
    regime = ctx.get('regime', '').upper()
    bias = ctx.get('bias_h4', '').upper()
    vol = ctx.get('vol_status', '').upper()
    if "EXHAUSTED" in vol: return "❌ WAIT / NO ENTRY (Jenuh)"
    if "EXPANSION" in regime:
        if "BULLISH" in bias: return "✅ BUY ONLY (Trending)"
        if "BEARISH" in bias: return "✅ SELL ONLY (Trending)"
    if "TRANSITION" in regime: return "🔄 SCALPING OK (Range)"
    return "👀 MONITOR ONLY"

# --- 2. SERVER KEEP-ALIVE ---
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

# --- 3. MASTER REPORT GENERATOR ---
async def generate_market_report(title="MARKET INTELLIGENCE REPORT"):
    """Laporan Gabungan: Teknikal + Strategi + Performa."""
    pairs = {"GOLD (XAUUSD)": "GC=F", "EURUSD": "EURUSD=X"}
    session = get_session_name()
    response = f"<b>🔍 {title}</b>\n🕒 Session: <b>{session}</b>\n━━━━━━━━━━━━━━━━━━\n\n"
    for name, sym in pairs.items():
        ctx = get_market_context(sym)
        if ctx:
            curr = float(ctx['price'])
            perf = calculate_performance(name, curr, float(ctx.get('open_price', curr)))
            action = derive_action(ctx)
            response += f"🏆 <b>{name}</b>\n"
            response += f"Perf (D)   : <b>{perf}</b>\n"
            response += f"Score      : {ctx['score']}\n"
            response += f"Bias H4    : {ctx['bias_h4']}\n"
            response += f"Regime     : {ctx['regime']}\n"
            response += f"Volatility : {ctx['vol_status']}\n"
            response += f"Price      : <code>{ctx['price']}</code>\n\n"
            response += f"🎯 <b>Action:</b>\n<code>{action}</code>\n"
            response += "──────────────────\n\n"
        else: response += f"❌ <b>{name}</b>: Data Offline.\n\n"
    return response

# --- 4. TEMPLATE COMMAND /NEWS ---
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Template berita dengan pemisah visual yang rapi."""
    events = get_risk_events()
    target = update.message if update.message else update.callback_query.message
    if not events:
        await target.reply_text("📭 Tidak ada berita High Impact.", parse_mode='HTML')
        return
    response = "<b>🗓 TRADING PLAN & NEWS</b>\n"
    response += "━━━━━━━━━━━━━━━━━━\n\n"
    for e in events:
        response += f"🕒 <code>{e['time']}</code> | <b>{e['currency']}</b>\n"
        response += f"🏆 <b>{e['event']}</b>\n"
        response += f"📅 {e['date']}\n"
        response += "──────────────────\n"
    response += "\n⚠️ <i>Slippage & spread berpotensi melebar.</i>"
    await target.reply_text(response, parse_mode='HTML')

# --- 5. AUTOMATION JOBS (THE FULL SQUAD) ---
async def intelligence_monitor_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    pairs = {"GOLD": "GC=F", "EURUSD": "EURUSD=X"}
    for name, sym in pairs.items():
        ctx = get_market_context(sym)
        if not ctx: continue
        curr = float(ctx['price'])
        prev = context.bot_data.get(f"lp_{name}")
        if prev and abs(curr - prev) > (5.0 if name == "GOLD" else 0.0050):
            msg = f"🚨 <b>SPIKE ALERT: {name}</b>\nMagnitude: <code>{abs(curr-prev):.2f}</code>\nStatus: <b>HIGH RISK</b>\n\n🎯 <b>Action:</b>\n<code>WAIT / NO ENTRY</code>"
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')
        context.bot_data[f"lp_{name}"] = curr

async def session_alert_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    h = datetime.now(WIB).hour
    if h in [14, 22, 4]: 
        msg = f"🏁 <b>SESSION SUMMARY</b>\n{await generate_market_report('CLOSING REPORT')}"
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')
    elif h == 15: await context.bot.send_message(chat_id=chat_id, text="🚀 <b>LONDON OPEN</b>", parse_mode='HTML')
    elif h == 20: await context.bot.send_message(chat_id=chat_id, text="🇺🇸 <b>NY OPEN</b>", parse_mode='HTML')

async def weekly_report_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    report = await generate_market_report("WEEKLY CLOSING SUMMARY")
    await context.bot.send_message(chat_id=chat_id, text=f"📉 {report}", parse_mode='HTML')

async def news_monitor_job(context: ContextTypes.DEFAULT_TYPE):
    """Sistem Alert Berita: H-3 dan H-15 Menit."""
    chat_id = os.getenv("YOUR_CHAT_ID")
    events = get_risk_events()
    now = datetime.now(WIB)
    for e in events:
        diff = (e['datetime_obj'] - now).total_seconds()
        if 259140 <= diff <= 259200: # H-3
            msg = f"📅 <b>UPCOMING NEWS (H-3)</b>\n━━━━━━━━━━━━━━━━━━\n🏆 Event: <b>{e['event']}</b>\n🕒 Waktu: <code>{e['time']}</code> WIB\n📅 Tanggal: {e['date']}"
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')
        elif 840 <= diff <= 900: # 15m
            await context.bot.send_message(chat_id=chat_id, text=f"⚠️ <b>NEWS ALERT 15m</b>\n🏆 {e['event']}\n🕒 Jam: <code>{e['time']}</code> WIB", parse_mode='HTML')

# --- 6. HANDLERS & NAVIGATION ---
async def post_init(application: Application):
    await application.bot.set_my_commands([BotCommand("start", "Mulai"), BotCommand("cek", "Analisis"), BotCommand("news", "Berita")])

async def cek_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fungsi pusat untuk laporan market."""
    response = await generate_market_report()
    keyboard = [[InlineKeyboardButton("🔄 Refresh Harga", callback_data='refresh_harga')],
                [InlineKeyboardButton("📅 Cek News", callback_data='cek_news')]]
    target = update.message if update.message else update.callback_query.message
    await target.reply_text(response, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'refresh_harga':
        response = await generate_market_report()
        await query.edit_message_text(response, parse_mode='HTML', 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh Harga", callback_data='refresh_harga')]]))
    elif query.data == 'cek_news': await news_command(update, context)

async def handle_menu_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if t == "🔍 Cek Market": await cek_context(update, context)
    elif t == "📅 Jadwal News": await news_command(update, context)
    elif "Mode" in t: await update.message.reply_text(f"🎯 Mode: <b>{t.split()[0]}</b>", parse_mode='HTML')

# --- 7. MAIN ---
if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    if token:
        keep_alive()
        t_req = HTTPXRequest(connect_timeout=30, read_timeout=30)
        app = ApplicationBuilder().token(token).request(t_req).post_init(post_init).build()
        
        jq = app.job_queue

        async def run_morning_briefing(context: ContextTypes.DEFAULT_TYPE):
            chat_id = os.getenv("YOUR_CHAT_ID")
            report = await generate_market_report("MORNING BRIEFING")
            await context.bot.send_message(chat_id=chat_id, text=report, parse_mode='HTML')

        jq.run_daily(run_morning_briefing, time=time(hour=7, minute=0, tzinfo=WIB))
        jq.run_repeating(news_monitor_job, interval=60)
        jq.run_repeating(intelligence_monitor_job, interval=60)
        jq.run_repeating(session_alert_job, interval=3600)
        jq.run_daily(weekly_report_job, time=time(hour=23, minute=0, tzinfo=WIB), days=(4,))

        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            keyboard = [[KeyboardButton("🔍 Cek Market"), KeyboardButton("📅 Jadwal News")], 
                        [KeyboardButton("🎯 Focus Mode"), KeyboardButton("🔔 Normal Mode")]]
            await update.message.reply_text(
                "🚀 <b>Alpha Pro Online</b>", 
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True), 
                parse_mode='HTML'
            )

        app.add_handler(CommandHandler('start', start_command))
        app.add_handler(CommandHandler('news', news_command))
        app.add_handler(CommandHandler('cek', cek_context))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu_clicks))
        app.add_handler(CallbackQueryHandler(button_handler))
        
        print("🔥 Bot Alpha Pro v.2026 Stable Aktif!")
        app.run_polling(bootstrap_retries=-1)