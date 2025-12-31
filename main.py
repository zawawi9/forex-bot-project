import os, pytz
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
from scripts.technical_analysis import get_market_context
from scripts.risk_manager import get_risk_events

load_dotenv()
WIB = pytz.timezone('Asia/Jakarta')

# --- SERVER FOR RENDER HEALTH CHECK ---
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    # Render biasanya menggunakan port 8080 atau 10000
    port = int(os.environ.get('PORT', 7860))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- STATE TRACKING ---
last_market_states = {} 
last_prices = {}        
focus_mode = "NORMAL"   

# --- 1. SETTING TOMBOL MENU POJOK KIRI ---
async def post_init(application: Application):
    commands = [
        BotCommand("start", "Mulai/Restart Bot"),
        BotCommand("cek", "Analisis Market Saat Ini"),
        BotCommand("news", "Jadwal Berita High Impact"),
    ]
    await application.bot.set_my_commands(commands)

# --- 2. FUNGSI GENERATE REPORT (HTML MODE) ---
async def generate_market_report():
    pairs = {"GOLD (XAUUSD)": "GC=F", "EURUSD": "EURUSD=X"}
    response = "<b>🔍 MARKET STATE REPORT</b>\n"
    response += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for name, sym in pairs.items():
        ctx = get_market_context(sym)
        if ctx:
            response += f"🏆 <b>{name}</b>\n"
            response += f"💰 Score: <b>{ctx['score']}</b>\n"
            response += f"💵 Price: <code>{ctx['price']}</code>\n"
            response += f"📈 Bias H4: <b>{ctx['bias_h4']}</b>\n"
            response += f"🔗 Alignment: {ctx['alignment']}\n"
            response += f"🏢 Regime: <i>{ctx['regime']}</i>\n"
            response += f"⚡ Range: {ctx['exhaust_pct']} | {ctx['vol_status']}\n"
            response += "──────────────────\n\n"
        else:
            response += f"❌ <b>{name}</b>: Data belum stabil.\n\n"
    return response

# --- 3. FUNGSI NEWS COMMAND ---
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message if update.message else update.callback_query.message
    events = get_risk_events()
    
    if not events:
        await target.reply_text("📭 Tidak ada berita High Impact terdeteksi.", parse_mode='HTML')
        return

    response = "<b>🗓 TRADING PLAN & NEWS CONTEXT</b>\n"
    response += "━━━━━━━━━━━━━━━━━━\n\n"
    for e in events:
        context_msg = "Berita High Impact. Potensi slippage dan spread melebar."
        if e.get('currency') == 'EUR': context_msg = "Berita zona Euro. Berdampak langsung pada EURUSD."
        elif "FOMC" in e['event']: context_msg = "Suku bunga USD. Volatilitas ekstrim!"

        response += f"🕒 <code>{e['time']}</code> | <b>{e['currency']}</b>\n"
        response += f"🏆 <b>{e['event']}</b>\n"
        response += f"ℹ️ <i>{context_msg}</i>\n"
        response += f"📅 {e['date']}\n"
        response += "──────────────────\n"
    
    response += "\n⚠️ <i>Trading saat news memiliki risiko tinggi.</i>"
    await target.reply_text(response, parse_mode='HTML')

# --- 4. MENU KEYBOARD LAYOUT ---
def get_main_menu():
    keyboard = [
        [KeyboardButton("🔍 Cek Market"), KeyboardButton("📅 Jadwal News")],
        [KeyboardButton("🎯 Focus Mode"), KeyboardButton("🔔 Normal Mode"), KeyboardButton("🔕 Silent Mode")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- 5. AUTOMATION JOBS ---
async def news_monitor_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    if not chat_id: return
    events = get_risk_events()
    now = datetime.now(WIB)
    for e in events:
        diff = e['datetime_obj'] - now
        if 840 <= diff.total_seconds() <= 900:
            msg = f"⚠️ <b>NEWS ALERT: 15 MENIT LAGI!</b>\n\n🏆 Event: <b>{e['event']}</b>\n🕒 Jam: <code>{e['time']}</code> WIB"
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')

async def daily_briefing_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    if chat_id:
        report = await generate_market_report()
        await context.bot.send_message(chat_id=chat_id, text=f"🌅 <b>MORNING BRIEFING</b>\n\n{report}", parse_mode='HTML')

async def session_alert_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("YOUR_CHAT_ID")
    if not chat_id or focus_mode == "SILENT": return
    current_hour = datetime.now(WIB).hour
    msg = ""
    if current_hour == 15: msg = "🚀 <b>LONDON SESSION OPEN</b>\nPerhatikan Liquidity Grab di High/Low Asia!"
    elif current_hour == 20: msg = "🇺🇸 <b>NEW YORK SESSION OPEN</b>\nHigh Volatility Expected!"
    if msg: await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')

async def intelligence_monitor_job(context: ContextTypes.DEFAULT_TYPE):
    global last_market_states, last_prices
    chat_id = os.getenv("YOUR_CHAT_ID")
    if not chat_id or focus_mode == "SILENT": return
    pairs = {"GOLD": "GC=F", "EURUSD": "EURUSD=X"}
    for name, sym in pairs.items():
        ctx = get_market_context(sym)
        if not ctx: continue
        curr_price = float(ctx['price'])
        if name in last_prices:
            diff = abs(curr_price - last_prices[name])
            threshold = 5.0 if name == "GOLD" else 0.0050
            if diff > threshold:
                await context.bot.send_message(chat_id=chat_id, text=f"🚨 <b>SPIKE: {name}</b> <code>{diff:.2f}</code>", parse_mode='HTML')
        last_prices[name] = curr_price

# --- 6. COMMAND & MENU HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🚀 <b>Bot Forex Alpha Aktif!</b>\nID: <code>{update.effective_chat.id}</code>",
        reply_markup=get_main_menu(),
        parse_mode='HTML'
    )

async def handle_menu_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔍 Cek Market":
        await cek_context(update, context)
    elif text == "📅 Jadwal News":
        await news_command(update, context)
    elif "Mode" in text:
        global focus_mode
        focus_mode = text.split()[0].upper()
        await update.message.reply_text(f"🎯 Mode diatur ke: <b>{focus_mode}</b>", parse_mode='HTML')

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
    elif query.data == 'cek_news':
        await news_command(update, context)

# --- 7. MAIN EXECUTION ---
if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    if token:
        app = ApplicationBuilder().token(token).post_init(post_init).build()
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
        
        print("🔥 Bot HTML-Professional Mode Aktif!")
        # Jalankan server web untuk keep-alive
        keep_alive()
        # Jalankan polling bot
        app.run_polling()