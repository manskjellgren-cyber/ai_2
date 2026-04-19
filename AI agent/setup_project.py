import sqlite3
import chromadb
import os

def setup():
    # 1. Rensa gamla databaser för att undvika krockar
    if os.path.exists("live_data.db"): os.remove("live_data.db")
    
    # 2. Setup ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name="customer_sla")
    
    for i in range(10):
        name = f"Kund {chr(65+i)}"
        cost = (i + 1) * 150
        collection.upsert(
            documents=[f"SLA för {name}: {cost} SEK/min"],
            metadatas=[{"customer": name, "cost_per_min": cost}],
            ids=[f"id_{i}"]
        )
    
    # 3. Setup SQL tabeller
    conn = sqlite3.connect("live_data.db")
    conn.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value INTEGER)")
    conn.execute("INSERT INTO settings VALUES ('sensitivity', 5)")
    conn.execute("CREATE TABLE port_status (customer TEXT PRIMARY KEY, status INTEGER, isolated_since TEXT)")
    conn.execute("CREATE TABLE logs (time TEXT, customer TEXT, traffic REAL, description TEXT, cost_loss REAL)")
    
    for i in range(10):
        conn.execute("INSERT INTO port_status VALUES (?, 0, NULL)", (f"Kund {chr(65+i)}",))
    
    conn.commit()
    conn.close()
    print("✅ Projektet är nollställt och ChromaDB är redo!")

if __name__ == "__main__":
    setup()