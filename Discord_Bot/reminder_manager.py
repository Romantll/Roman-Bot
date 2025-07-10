import json
from datetime import datetime
import os

REMINDER_FILE = 'comeback_reminders.json'

def load_reminders():
    if not os.path.exists(REMINDER_FILE):
        return []
    with open(REMINDER_FILE, 'r') as file:
        return json.load(file)
    
def save_reminders(reminders):
    with open(REMINDER_FILE, 'w') as file:
        json.dump(reminders, file, indent=2)

def add_reminder(user_id, channel_id, group, date_str, time_str, title=None):
    try:
        # Fromat YYYY-MM-DD HH:MM
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        dt_utc = dt.astimezone().astimezone(datetime.utcnow().tzinfo) # For UTC conversion

        reminders = load_reminders()
        reminders.append({
            "user_id": user_id,
            "channel_id": channel_id,
            "datetime_utc": dt_utc.isoformat(),
            "group": group,
            "title": title or "",
        })

        save_reminders(reminders)
        
        return True
    except Exception as e:
        return False, str(e)