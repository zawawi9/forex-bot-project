# 📊 Forex Market Context & Risk Awareness Tool

Bot Telegram berbasis Python yang dirancang untuk membantu trader mengklasifikasikan kondisi pasar (Market Regime) dan memantau risiko fundamental secara otomatis. 

Berbeda dengan bot trading biasa, alat ini **bukanlah alat prediksi (signal bot)**, melainkan alat bantu navigasi untuk memahami bias arah, kekuatan tren, dan volatilitas pasar.

---

## 🛠 Fitur Utama

- **Market State Classifier**: Mengklasifikasikan kondisi pasar menggunakan indikator teknikal:
  - **Directional Bias**: Menggunakan EMA 30 & EMA 60 (Strategy Madro H4).
  - **Trend Strength**: Menggunakan Average Directional Index (ADX 14).
  - **Volatility Measurement**: Menggunakan Average True Range (ATR 14).
- **Risk Event Monitor**: Mendeteksi jadwal rilis berita *high-impact* (NFP, FOMC, CPI) untuk memberikan peringatan dini (Risk Window).
- **AI-Powered Context**: Mengintegrasikan Google Gemini AI untuk merangkum dampak fundamental terhadap teknikal.
- **Support Multiple Pairs**: Fokus pada XAUUSD (Gold) dan EURUSD pada timeframe H4.

---

## 🧠 Filosofi Strategi

Bot ini dibangun berdasarkan prinsip bahwa **"Konteks lebih penting daripada Prediksi"**.
1. **ADX < 20**: Market dianggap *Sideways/Chop*, sinyal crossover EMA akan diabaikan.
2. **ADX > 25**: Market dianggap *Trending*, bias EMA menjadi relevan.
3. **High Impact News**: Saat berita besar akan rilis, bot akan mengaktifkan *Risk Flag* karena reliabilitas teknikal cenderung menurun drastis.

---

## 📁 Struktur Folder

```text
forex-bot-project/
├── scripts/
│   ├── technical_analysis.py  # Logika perhitungan ADX, ATR, EMA
│   ├── risk_manager.py       # Scraping kalender ekonomi
│   └── ai_engine.py          # Integrasi Gemini AI
├── main.py                   # Entry point Bot Telegram
├── .env                      # API Keys (Hidden)
└── requirements.txt          # Library dependencies
```

---

## 🚀 Cara Instalasi
#### 1. Clone Repository ini
```
git clone [https://github.com/zawawi9/forex-bot-project.git](https://github.com/zawawi9/forex-bot-project.git)
cd forex-bot-project
```
#### 2.Buat Virtual Environment
```
python -m venv venv
source venv/bin/activate  # Untuk Windows: .\venv\Scripts\activate
```
#### 3.Instal Dependencies
```
pip install -r requirements.txt
```
#### 4.Konfigurasi API Keys Buat file .env dan masukkan token Anda:
```
TELEGRAM_TOKEN=your_token_here
GEMINI_API_KEY=your_key_here
```
#### 5.Jalankan Bot
```
python main.py
```

---

# ⚠️ Disclaimer
Alat ini dibuat hanya untuk tujuan edukasi dan membantu analisis data. Keputusan trading sepenuhnya berada di tangan pengguna. Pastikan anda memahami risiko trading forex sebelum melakukan eksekusi di akun rill.
