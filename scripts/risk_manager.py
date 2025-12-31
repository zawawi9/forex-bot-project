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
        upcoming_events = []
        wib = pytz.timezone('Asia/Jakarta')
        now_wib = datetime.now(wib)
        for event in data:
            currency = event.get('country')
            impact = event.get('impact')
            if impact in ['High', 'Medium'] and currency in ['USD', 'EUR']:
                try:
                    raw_date = event.get('date')
                    clean_date_str = raw_date[:19]
                    dt_obj = datetime.strptime(clean_date_str, "%Y-%m-%dT%H:%M:%S")
                    dt_utc = pytz.utc.localize(dt_obj)
                    dt_wib = dt_utc.astimezone(wib)
                    if dt_wib > now_wib:
                        upcoming_events.append({
                            "event": event.get('title'),
                            "time": dt_wib.strftime("%H:%M"),
                            "date": dt_wib.strftime("%d %b %Y"),
                            "currency": currency,
                            "datetime_obj": dt_wib
                        })
                except:
                    continue
        upcoming_events.sort(key=lambda x: x['datetime_obj'])
        return upcoming_events[:8]

    except Exception as e:
        print(f"Error fetching news: {e}")
        return []