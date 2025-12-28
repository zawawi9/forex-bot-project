# 📈 Forex Alpha Context Bot

Bot Telegram asisten trading yang menggabungkan Analisis Teknikal (H4) dan Kalender Ekonomi Fundamental (WIB) secara real-time.

---

## ✨ Fitur Utama
- **Technical Analysis (`/cek`)**: Mengklasifikasi kondisi market XAUUSD & EURUSD menggunakan EMA 30/60, ADX, dan ATR pada timeframe H4.
- **Economic Calendar (`/news`)**: Menampilkan jadwal berita High Impact (Merah) dari Forex Factory yang otomatis dikonversi ke zona waktu **WIB**.
- **Trading Recommendations**: Memberikan saran manajemen risiko sebelum, saat, dan sesudah berita penting muncul.
- **Modular Structure**: Kode rapi dengan pemisahan logika indikator, berita, dan bot utama.

---

## 🛠️ Teknologi & Library
- [Python 3.10+](https://www.python.org/)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Interface Bot
- [yfinance](https://github.com/ranaroussi/yfinance) - Data Market Real-time
- [pandas-ta](https://github.com/twopirllc/pandas-ta) - Indikator Teknikal
- [pytz](https://pythonhosted.org/pytz/) - Konversi Zona Waktu WIB

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
```
#### 5.Jalankan Bot
```
python main.py
```

---

# ⚠️ Disclaimer
Alat ini dibuat hanya untuk tujuan edukasi dan membantu analisis data. Keputusan trading sepenuhnya berada di tangan pengguna. Pastikan anda memahami risiko trading forex sebelum melakukan eksekusi di akun rill.
