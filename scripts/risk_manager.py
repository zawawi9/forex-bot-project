import requests
from datetime import datetime, timedelta
import pytz

def get_risk_events():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return []

        data = response.json()
        risk_list = []
        wib = pytz.timezone('Asia/Jakarta')

        for event in data:
            currency = event.get('country')
            impact = event.get('impact')
            
            if event.get('impact') in ['High', 'Medium'] and event.get('country') in ['USD', 'EUR']:
                try:
                    raw_date = event.get('date')
                    clean_date_str = raw_date[:19]
                    dt_obj = datetime.strptime(clean_date_str, "%Y-%m-%dT%H:%M:%S")
                    
                    # Koreksi WIB (+12 Jam dari data API)
                    dt_wib = dt_obj + timedelta(hours=12)
                    
                    jam_tampil = dt_wib.strftime("%H:%M")
                    tgl_tampil = dt_wib.strftime("%d %b %Y")
                except:
                    jam_tampil = "Cek Web"; tgl_tampil = "N/A"

                risk_list.append({
                    "event": event.get('title'),
                    "time": jam_tampil,
                    "date": tgl_tampil,
                    "currency": currency
                })
        return risk_list[:8]
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []