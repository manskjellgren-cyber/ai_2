import time, chromadb, joblib, sqlite3, os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. LADDA MODELLER
models = {"RF": joblib.load('rf_model.pkl'), "LR": joblib.load('lr_model.pkl'), "GB": joblib.load('gb_model.pkl')}
scaler = joblib.load('scaler.pkl')
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# 2. CHROMA DB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
try:
    collection = chroma_client.get_collection(name="network_expert_knowledge")
except:
    collection = chroma_client.create_collection(name="network_expert_knowledge")
    print("✨ Ny Chroma-kollektion skapad!")

def setup_db():
    conn = sqlite3.connect("live_data.db")
    conn.execute("DROP TABLE IF EXISTS logs")
    conn.execute("CREATE TABLE logs (time TEXT, rf_score REAL, lr_score REAL, gb_score REAL, facit REAL, rag_score REAL, description TEXT)")
    conn.commit()
    return conn

def run_agent():
    conn = setup_db()
    data_file = 'kdd_test_data.txt' 
    
    # Läs filen (vi sätter inga namn än eftersom den är så bred)
    test_data = pd.read_csv(data_file, header=None)
    
    # MAPPNING AV INDEX (Baserat på din filstruktur)
    # 0: duration, 1: protocol, 4: src_bytes, 5: dst_bytes, 22: count, 28: diff_srv_rate
    feature_indices = [0, 4, 5, 22, 28, 1] 
    label_index = 41 # "näst sista kolumnen" där ordet (neptune, normal) finns
    
    protocol_map = {'tcp': 1.0, 'udp': 2.0, 'icmp': 3.0, 'normal': 1.0}
    
    step = 0
    print(f"🚀 AGENT AKTIV: Läser NSL-KDD format från {data_file}")

    while True:
        row = test_data.iloc[step % len(test_data)].copy()
        
        # 1. Hämta etiketten (ordet på index 41)
        raw_label = str(row[label_index]).replace('.', '').strip().lower()
        is_attack_facit = 1.0 if raw_label != 'normal' else 0.0
        
        # 2. Förbered ML-data (Plocka rätt kolumner och konvertera protokoll)
        ml_row = row[feature_indices].values
        # ml_row[5] är protocol_type
        p_type = str(ml_row[5]).lower().strip()
        ml_row[5] = protocol_map.get(p_type, 1.0)
        
        # Skapa DataFrame med namnen scalern förväntar sig
        X_raw = pd.DataFrame([ml_row], columns=['duration', 'src_bytes', 'dst_bytes', 'count', 'diff_srv_rate', 'protocol_type'])
        
        # 3. ML-Analys
        X_scaled = scaler.transform(X_raw)[0]
        scores = {name: m.predict_proba([X_scaled])[0][1] for name, m in models.items()}
        
        # 4. RAG-Analys
        rag_match_val = 0.0
        # Beskrivning för RAG-sökning
        obs_summary = f"D:{row[0]} B:{row[4]} C:{row[22]}"
        query_vec = embedder.encode(obs_summary).tolist()
        results = collection.query(query_embeddings=[query_vec], n_results=1)
        
        diag = "STATUS: Normal"
        action_info = "ÖVERVAKAR"

        # RAG Logik: Kolla om vi känner igen namnet (t.ex. neptune)
        if results['distances'] and len(results['distances'][0]) > 0:
            if results['distances'][0][0] < 0.4:
                meta = results['metadatas'][0][0]
                if is_attack_facit == 1.0:
                    rag_match_val = 1.0
                    diag = f"DIAGNOS: {meta['cause']}"
                    action_info = f"ÅTGÄRD: Blockera {raw_label}"

        # Inlärning: Om ny attack upptäcks
        if is_attack_facit == 1.0 and rag_match_val == 0.0:
            diag = f"NYUPPTÄCKT: {raw_label.upper()}"
            action_info = "AUTO_LEARN: Loggar hotmönster"
            collection.add(
                embeddings=[query_vec], 
                metadatas=[{"cause": raw_label.capitalize()}], 
                ids=[f"id_{raw_label}_{step % 100}"]
            )

        # 5. SPARA TILL SQL
        timestamp = time.strftime("%H:%M:%S")
        full_desc = f"{diag} | {action_info}"
        conn.execute("INSERT INTO logs VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (timestamp, scores['RF'], scores['LR'], scores['GB'], 
                      is_attack_facit, rag_match_val, full_desc))
        conn.commit()
        
        # Print i terminalen för kontroll
        print(f"[{timestamp}] Rad {step} | Label: {raw_label:10} | RAG: {rag_match_val}")
        
        step += 1
        time.sleep(1.2)

if __name__ == "__main__":
    run_agent()