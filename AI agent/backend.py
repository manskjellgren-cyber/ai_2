# Skrivs i VS Code eller Notepad. Körs i terminalen: python backend.py
# Förklaring: Detta är projektets "hjärta" som aldrig sover. Det använder .pkl-filen för att fatta beslut och sparar allt i en SQLite-databas.


import time, joblib, sqlite3, pandas as pd
from datetime import datetime

model = joblib.load("student_model.pkl")
conn = sqlite3.connect("live_data.db", check_same_thread=False)
cursor = conn.cursor()

# Initiera databastabeller
cursor.execute("CREATE TABLE IF NOT EXISTS logs (time TEXT, traffic REAL, action INTEGER, cost REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val INTEGER)")
cursor.execute("INSERT OR IGNORE INTO settings VALUES ('kill_switch', 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS finance (total REAL)")
cursor.execute("INSERT OR IGNORE INTO finance VALUES (0.0)")
conn.commit()

while True:
    # 1. Läs inställningar
    cursor.execute("SELECT val FROM settings WHERE key='kill_switch'")
    kill_active = cursor.fetchone()[0]
    
    # 2. Simulera live-trafik
    current_traffic = 600 if time.time() % 30 < 2 else 40 # Attack var 30:e sek
    pred = model.predict(pd.DataFrame([[current_traffic]], columns=['traffic']))[0]
    
    # 3. Beräkna kostnad (SLA Guld: 5000kr/min = 83kr/sek)
    current_penalty = 83.0 if pred == 1 and not kill_active else 0
    
    # 4. Spara data
    cursor.execute("INSERT INTO logs VALUES (?, ?, ?, ?)", 
                   (datetime.now().strftime("%H:%M:%S"), current_traffic, int(pred), current_penalty))
    cursor.execute("UPDATE finance SET total = total + ?", (current_penalty,))
    conn.commit()
    
    time.sleep(1)