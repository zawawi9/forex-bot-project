import yfinance as yf
import pandas as pd
import pandas_ta as ta

def get_market_context(symbol):
    try:
        # 1. Tarik Data Multi-Timeframe
        df_h4 = yf.download(symbol, interval="4h", period="1mo", progress=False)
        df_d1 = yf.download(symbol, interval="1d", period="6mo", progress=False)

        if df_h4.empty or df_d1.empty: return None

        # Cleaning Multi-index
        if isinstance(df_h4.columns, pd.MultiIndex):
            df_h4.columns = df_h4.columns.get_level_values(0)
            df_d1.columns = df_d1.columns.get_level_values(0)

        # 2. Indikator H4
        df_h4['EMA30'] = ta.ema(df_h4['Close'], length=30)
        df_h4['EMA60'] = ta.ema(df_h4['Close'], length=60)
        adx_df = ta.adx(df_h4['High'], df_h4['Low'], df_h4['Close'], length=14)
        atr_df = ta.atr(df_h4['High'], df_h4['Low'], df_h4['Close'], length=14)

        # 3. Indikator Daily
        df_d1['EMA50'] = ta.ema(df_d1['Close'], length=50)
        
        last_h4 = df_h4.iloc[-1]
        last_d1 = df_d1.iloc[-1]
        current_price = last_h4['Close']

        # --- ELITE LOGIC 1: BIAS ALIGNMENT ---
        bias_h4 = "BULLISH" if last_h4['EMA30'] > last_h4['EMA60'] else "BEARISH"
        bias_d1 = "BULLISH" if current_price > last_d1['EMA50'] else "BEARISH"
        is_aligned = bias_h4 == bias_d1
        alignment = "✅ ALIGNED" if is_aligned else "⚠️ CONTRA"

        # --- ELITE LOGIC 2: MARKET REGIME ---
        adx_val = adx_df.iloc[-1]['ADX_14']
        if adx_val < 20: regime = "COMPRESSION (Sideways)"
        elif adx_val > 25: regime = "EXPANSION (Trending)"
        else: regime = "TRANSITION"
        daily_range = df_h4.iloc[-6:]['High'].max() - df_h4.iloc[-6:]['Low'].min()
        atr_val = atr_df.iloc[-1]
        exhaustion_pct = (daily_range / (atr_val * 2)) * 100 # Normal range biasanya 2x ATR H4
        
        exhaustion_status = "NORMAL"
        if exhaustion_pct > 85: exhaustion_status = "⚠️ EXHAUSTED (Buyer/Seller Tired)"

        # --- ELITE LOGIC 4: CONFIDENCE SCORE ---
        score_val = 0
        if is_aligned: score_val += 2
        if adx_val > 25: score_val += 1
        if exhaustion_pct < 80: score_val += 1
        
        if score_val >= 3: score = "🟢 HIGH (Favorable)"
        elif score_val == 2: score = "🟡 MEDIUM (Neutral)"
        else: score = "🔴 LOW (High Risk)"

        # Format harga
        decimal = 5 if "EURUSD" in symbol else 2

        return {
            "price": f"{current_price:.{decimal}f}",
            "bias_h4": bias_h4,
            "alignment": alignment,
            "regime": regime,
            "vol_status": exhaustion_status,
            "adx": f"{adx_val:.1f}",
            "score": score,
            "exhaust_pct": f"{exhaustion_pct:.0f}%"
        }
    except Exception as e:
        print(f"Error Technical: {e}")
        return None