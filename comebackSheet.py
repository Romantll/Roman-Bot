import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def get_upcoming_comebacks(sheet_name="Kpop Comebacks"):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("kpop-comebacks-credentials.json", scope)

    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1

    rows = sheet.get_all_records()
    today = datetime.now().date()
    result = []

    for row in rows:
        try:
            date = datetime.strptime(row["Date"], "%Y-%m-%d").date()
            if date >= today:
                result.append(f"{row['Group']} – {row['Title']} – {row['Date']} at {row['Time']}")
        except:
            continue

    return result
