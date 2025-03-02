import requests
import time
import os

# Basis-URL
base_url = "https://westfaelisches-landestheater.de/repertoire/?produktion_id="

# Dateien
last_id_file = "last_id.txt"
found_file = "found_ids.txt"

# Letzten Status laden oder bei 0 anfangen
if os.path.exists(last_id_file):
    with open(last_id_file, "r") as f:
        start_id = int(f.read().strip())
else:
    start_id = 0

# Startzeit erfassen
start_time = time.time()

# Session verwenden für schnellere Requests
session = requests.Session()

current_id = start_id
found_urls_buffer = []
save_interval = 50  # alle 50 IDs zwischenspeichern

try:
    while True:
        # Aktuelle Laufzeit berechnen
        elapsed_time = time.time() - start_time
        # Fortschrittsanzeige
        print(f"[Laufzeit: {elapsed_time:.2f} Sekunden] Prüfe ID {current_id}...")

        url = base_url + str(current_id)
        response = session.get(url)

        if response.status_code == 200:
            page_content = response.text
            # Prüfen, ob die Seite den Hinweis auf keine Aufführungstermine enthält
            if "Derzeit noch keine Aufführungstermine" not in page_content:
                found_urls_buffer.append(url)
        # Keine else-Bearbeitung, da wir einfach nur weiter machen.

        # In regelmäßigen Abständen speichern
        if current_id % save_interval == 0 and current_id > start_id:
            # Gefundene URLs in Datei schreiben
            if found_urls_buffer:
                with open(found_file, "a") as f:
                    for fu in found_urls_buffer:
                        f.write(fu + "\n")
                found_urls_buffer.clear()

            # Letzten Stand speichern
            with open(last_id_file, "w") as f:
                f.write(str(current_id))

        current_id += 1

        # Falls Sie den Server nicht überlasten wollen, können Sie die Zeit hier reduzieren (z. B. sleep(0.1))
        # time.sleep(0.1)

except KeyboardInterrupt:
    # Beim manuellen Abbruch noch den aktuellen Stand speichern
    with open(last_id_file, "w") as f:
        f.write(str(current_id))
    if found_urls_buffer:
        with open(found_file, "a") as f:
            for fu in found_urls_buffer:
                f.write(fu + "\n")
    print("\nSkript manuell beendet. Letzter geprüfter ID war:", current_id)
