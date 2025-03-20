import sqlite3
import requests
from bs4 import BeautifulSoup
import os
import time
from fastapi import FastAPI

app = FastAPI()

# Datenbank initialisieren
def init_db():
    conn = sqlite3.connect("theater.db")
    cursor = conn.cursor()
    
    cursor.executescript('''
    DROP TABLE IF EXISTS stuecke;
    DROP TABLE IF EXISTS besetzung;
    DROP TABLE IF EXISTS inszenierungsteam;
    DROP TABLE IF EXISTS medien;
    DROP TABLE IF EXISTS auffuehrungen;
    
    CREATE TABLE stuecke (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titel TEXT,
        autor TEXT,
        altersempfehlung TEXT,
        dauer TEXT,
        beschreibung TEXT
    );
    
    CREATE TABLE besetzung (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stueck_id INTEGER,
        rolle TEXT,
        name TEXT,
        FOREIGN KEY (stueck_id) REFERENCES stuecke(id)
    );
    
    CREATE TABLE inszenierungsteam (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stueck_id INTEGER,
        position TEXT,
        name TEXT,
        FOREIGN KEY (stueck_id) REFERENCES stuecke(id)
    );
    
    CREATE TABLE medien (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stueck_id INTEGER,
        typ TEXT,
        url TEXT,
        FOREIGN KEY (stueck_id) REFERENCES stuecke(id)
    );
    
    CREATE TABLE auffuehrungen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stueck_id INTEGER,
        datum TEXT,
        uhrzeit TEXT,
        ort TEXT,
        FOREIGN KEY (stueck_id) REFERENCES stuecke(id)
    );
    ''')
    
    conn.commit()
    conn.close()

# Funktion zum Extrahieren der Daten aus einer URL
def scrape_stueck(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Fehler beim Abrufen von {url}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    titel = soup.find("h1", class_="typo-xl color-main").text.strip() if soup.find("h1", class_="typo-xl color-main") else "Unbekannt"
    autor = soup.find("span", class_="typo-xl color-main-1").text.strip() if soup.find("span", class_="typo-xl color-main-1") else "Unbekannt"
    altersempfehlung = " | ".join([el.text.strip() for el in soup.find_all("div", class_="detail-beschreibung-title")])
    dauer_element = soup.find(text="Stückdauer:")
    dauer = dauer_element.find_next("strong").text.strip() if dauer_element else "Unbekannt"
    
    beschreibung = "\n".join([p.text.strip() for p in soup.find_all("p")])
    
    # Medien extrahieren
    bilder = [img["src"] for img in soup.select(".detail-image-box img")]
    audio = [source["src"] for source in soup.select("audio source")]
    video = [f"https://www.youtube.com/watch?v={div['data-plyr-embed-id']}" for div in soup.select(".video")]
    
    # Inszenierungsteam
    inszenierungsteam = []
    for span in soup.select(".detail-cast span")[-5:]:
        position = span.find("strong").text.strip()
        name = span.find("a").text.strip()
        inszenierungsteam.append((position, name))
    
    # Aufführungen
    auffuehrungen = []
    for li in soup.select(".detail-beschreibung-terminliste li"):
        datum = li.select_one(".span-2").text.strip()
        uhrzeit = li.select_one(".span-2.last").text.strip()
        ort = li.select_one(".span-7").text.strip()
        auffuehrungen.append((datum, uhrzeit, ort))
    
    return {
        "titel": titel,
        "autor": autor,
        "altersempfehlung": altersempfehlung,
        "dauer": dauer,
        "beschreibung": beschreibung,
        "inszenierungsteam": inszenierungsteam,
        "medien": bilder + audio + video,
        "auffuehrungen": auffuehrungen
    }

# Funktion zum Speichern der Daten in die Datenbank
def save_to_db(data):
    conn = sqlite3.connect("theater.db")
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO stuecke (titel, autor, altersempfehlung, dauer, beschreibung) VALUES (?, ?, ?, ?, ?)",
                   (data["titel"], data["autor"], data["altersempfehlung"], data["dauer"], data["beschreibung"]))
    stueck_id = cursor.lastrowid
    
    for position, name in data["inszenierungsteam"]:
        cursor.execute("INSERT INTO inszenierungsteam (stueck_id, position, name) VALUES (?, ?, ?)", (stueck_id, position, name))
    
    for url in data["medien"]:
        typ = "bild" if url.endswith(".jpg") or url.endswith(".png") else "audio" if url.endswith(".mp3") else "video"
        cursor.execute("INSERT INTO medien (stueck_id, typ, url) VALUES (?, ?, ?)", (stueck_id, typ, url))
    
    for datum, uhrzeit, ort in data["auffuehrungen"]:
        cursor.execute("INSERT INTO auffuehrungen (stueck_id, datum, uhrzeit, ort) VALUES (?, ?, ?, ?)", (stueck_id, datum, uhrzeit, ort))
    
    conn.commit()
    conn.close()

@app.post("/fill-db")
def fill_db():
    init_db()
    with open("stuecke_urls.txt", "r") as file:
        urls = file.readlines()
    
    for url in urls:
        url = url.strip()
        print(f"Verarbeite: {url}")
        data = scrape_stueck(url)
        if data:
            save_to_db(data)
        time.sleep(2)  # Vermeidung von Server-Sperren
    
    return {"message": "Datenbank wurde mit den Stücken gefüllt."}

@app.get("/stuecke")
def get_stuecke():
    conn = sqlite3.connect("theater.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM stuecke")
    stuecke = cursor.fetchall()
    
    result = []
    for stueck in stuecke:
        stueck_id, titel, autor, altersempfehlung, dauer, beschreibung = stueck
        
        # Inszenierungsteam abrufen
        cursor.execute("SELECT position, name FROM inszenierungsteam WHERE stueck_id = ?", (stueck_id,))
        inszenierungsteam = [{"position": pos, "name": name} for pos, name in cursor.fetchall()]
        
        # Medien abrufen
        cursor.execute("SELECT typ, url FROM medien WHERE stueck_id = ?", (stueck_id,))
        medien = [{"typ": typ, "url": url} for typ, url in cursor.fetchall()]
        
        # Aufführungen abrufen
        cursor.execute("SELECT datum, uhrzeit, ort FROM auffuehrungen WHERE stueck_id = ?", (stueck_id,))
        auffuehrungen = [{"datum": datum, "uhrzeit": uhrzeit, "ort": ort} for datum, uhrzeit, ort in cursor.fetchall()]
        
        result.append({
            "id": stueck_id,
            "titel": titel,
            "autor": autor,
            "altersempfehlung": altersempfehlung,
            "dauer": dauer,
            "beschreibung": beschreibung,
            "inszenierungsteam": inszenierungsteam,
            "medien": medien,
            "auffuehrungen": auffuehrungen
        })
    
    conn.close()
    return {"stuecke": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
