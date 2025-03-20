import csv
import sqlite3
from bs4 import BeautifulSoup
import requests

html = """PASTE_YOUR_HTML_HERE"""

# Liste mit den URLs der Stücke
stuecke_links = [
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=1496",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=4517",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=4518",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=4519",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=4521",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=4523",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=5531",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=5540",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=5542",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=5543",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=5544",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=5546",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=5547",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=5548",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=8550",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=10560",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=10561",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=10562",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=10564",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=10565",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=10566",
    "https://westfaelisches-landestheater.de/repertoire/?produktion_id=10567"
]
events = []
for url in stuecke_links:
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for li in soup.select('.detail-beschreibung-terminliste li'):
            datum = li.select_one('strong').text.strip()
            uhrzeit = li.select_one('.last.rechts').text.strip()
            ort = li.select_one('.span-7').text.strip()
            google_maps_link = li.select_one('a')['href'] if li.select_one('a') else ""
            events.append((datum, uhrzeit, ort, google_maps_link))
    else:
        print(f"Fehler beim Abruf von {url}")

# Save to CSV
csv_filename = "theater_schedule.csv"
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Datum", "Uhrzeit", "Ort", "Google Maps Link"])
    writer.writerows(events)

print(f"CSV-Datei gespeichert: {csv_filename}")

# Save to SQLite database
db_filename = "theater_schedule.db"
conn = sqlite3.connect(db_filename)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Auffuehrungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Datum TEXT,
    Uhrzeit TEXT,
    Ort TEXT,
    `Google Maps Link` TEXT
)""")

cursor.executemany("""
INSERT INTO Auffuehrungen (Datum, Uhrzeit, Ort, `Google Maps Link`) 
VALUES (?, ?, ?, ?)""", events)

conn.commit()
conn.close()

print(f"SQL-Datenbank gespeichert: {db_filename}")
