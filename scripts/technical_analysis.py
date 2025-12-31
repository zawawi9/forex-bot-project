import yfinance as yf
import pandas as ta
import pandas_ta as ta_lib

def get_market_context(symbol):
    try:
        # 1. Ambil Data H4
        df_h4 = yf.download(symbol, interval="4h", period="1mo", progress=False)
        df_d1 = yf.download(symbol, interval="1d", period="6mo", progress=False)

        if df_h4.empty or df_d1.empty:
            return None

        # Bersihkan Multi-Index jika ada
        if isinstance(df_h4.columns, ta.MultiIndex):
            df_h4.columns = df_h4.columns.get_level_values(0)
            df_d1.columns = df_d1.columns.get_level_values(0)

        # 2. Perhitungan Indikator H4
        df_h4['EMA30'] = ta_lib.ema(df_h4['Close'], length=30)
        df_h4['EMA60'] = ta_lib.ema(df_h4['Close'], length=60)
        adx = ta_lib.adx(df_h4['High'], df_h4['Low'], df_h4['Close'], length=14)
        atr = ta_lib.atr(df_h4['High'], df_h4['Low'], df_h4['Close'], length=14)

        df_d1['EMA50'] = ta_lib.ema(df_d1['Close'], length=50)
        
        # 4. Ambil Data Terakhir
        last_h4 = df_h4.iloc[-1]
        last_d1 = df_d1.iloc[-1]
        current_price = last_h4['Close']

        bias_h4 = "BULLISH" if last_h4['EMA30'] > last_h4['EMA60'] else "BEARISH"
        bias_d1 = "BULLISH" if current_price > last_d1['EMA50'] else "BEARISH"
        
        alignment = "✅ ALIGNED" if bias_h4 == bias_d1 else "⚠️ CONTRA (Hati-hati)"

        adx_val = adx.iloc[-1]['ADX_14']
        if adx_val < 20:
            regime = "COMPRESSION (Sideways)"
        elif adx_val > 25:
            regime = "EXPANSION (Trending)"
        else:
            regime = "TRANSITION"

        day_range = last_h4['High'] - last_h4['Low'] # Sederhana untuk tes
        atr_val = atr.iloc[-1]
        volatility_status = "NORMAL" if day_range < (atr_val * 2) else "EXTREME"

        if symbol == "GC=F":
            display_price = current_price 
            decimal_places = 2
        else:
            display_price = current_price
            decimal_places = 5

        formatted_price = f"{display_price:.{decimal_places}f}"

        return {
            "price": formatted_price,
            "bias_h4": bias_h4,
            "alignment": alignment,
            "regime": regime,
            "vol_status": volatility_status,
            "adx": f"{adx_val:.1f}"
        }
    except Exception as e:
        print(f"Error di technical_analysis: {e}")
        return None