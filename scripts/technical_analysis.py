import yfinance as yf
import pandas_ta as ta

def get_market_context(symbol):
    # 1. Ambil data
    df = yf.download(symbol, interval="4h", period="1mo", progress=False)
    
    # Cek apakah data kosong atau terlalu sedikit
    if df is None or df.empty or len(df) < 30:
        return None

    try:
        # 2. Hitung Indikator
        df['EMA30'] = ta.ema(df['Close'], length=30)
        df['EMA60'] = ta.ema(df['Close'], length=60)
        adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        if adx_df is None or adx_df.empty:
            return None
            
        df['ADX'] = adx_df['ADX_14']
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        last = df.dropna().iloc[-1]
        
        # 3. Klasifikasi
        bias = "BULLISH" if last['EMA30'] > last['EMA60'] else "BEARISH"
        adx_val = last['ADX']
        
        if adx_val < 20: strength = "WEAK/SIDEWAYS"
        elif 20 <= adx_val < 40: strength = "HEALTHY TREND"
        else: strength = "OVEREXTENDED"
        
        regime = "TRENDING" if adx_val > 25 else "RANGING/CHOPPY"

        return {
            "bias": bias,
            "strength": strength,
            "regime": regime,
            "atr": round(last['ATR'], 4)
        }
    except Exception as e:
        print(f"Error calculating indicators for {symbol}: {e}")
        return None