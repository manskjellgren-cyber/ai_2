import time
import chromadb
import joblib
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import sqlite3

# --- 1. LADDA STATISKA MODELLER (De tre poliserna) ---
models = {
    "RF": joblib.load('rf_model.pkl'),
    "LR": joblib.load('lr_model.pkl'),
    "GB": joblib.load('gb_model.pkl')
}
scaler = joblib.load('scaler.pkl')
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# --- 2. ANSLUT TILL CHROMADB (Expertminnet) ---
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="network_expert_knowledge")

def get_rag_analysis(features):
    """
    Här sker Retrieval-steget. Vi översätter rå nätverksdata till en sökning.
    """
    # Vi skapar en beskrivning av vad vi ser just nu
    current_observation = f"Varaktighet: {features[0]}, Bytes: {features[1]}, Frekvens: {features[3]}, Skillnad: {features[4]}"
    
    # Skapa en vektor av observationen
    query_vec = embedder.encode(current_observation).tolist()
    
    # Sök i ChromaDB (RAG)
    results = collection.query(query_embeddings=[query_vec], n_results=1)
    
    # Om likheten är tillräckligt hög (avstånd < 1.0), returnera expertrådet
    if results['distances'][0][0] < 1.0:
        return results['metadatas'][0][0]
    return None

def run_loop():
    # Simulering av dataflöde
    test_data = pd.read_csv('skarp_test_data.txt')
    step = 0
    
    conn = sqlite3.connect("live_data.db")
    
    while True:
        row = test_data.iloc[step % len(test_data)]
        X_raw = pd.DataFrame([row.drop('label')], columns=row.index[:-1])
        X_scaled = scaler.transform(X_raw)[0]
        
        # --- STEG A: KONSENSUS-ANALYS (ML) ---
        # Vi låter de tre modellerna rösta
        votes = [m.predict_proba([X_scaled])[0][1] for m in models.values()]
        avg_conf = np.mean(votes)
        
        # --- STEG B: RAG-ANALYS (Hitta orsak & Action) ---
        analysis = None
        if avg_conf > 0.6: # Om vi har en misstänkt anomali
            analysis = get_rag_analysis(X_scaled)
        
        # --- STEG C: FORMULERA SVAR (Augmentation) ---
        if analysis:
            status = f"ANOMALI: {analysis['cause']}"
            action = f"KOD: {analysis['action']} | RÅD: {analysis['remediation']}"
        else:
            status = "NORMAL" if avg_conf < 0.4 else "MISSTÄNKT AKTIVITET"
            action = "INGEN ÅTGÄRD" if avg_conf < 0.4 else "MONITORERING_AKTIVERAD"

        # Spara till Dashboard (SQL)
        # Här skickar vi med den rika datan så att inget förenklas bort
        desc = f"{status} || {action}"
        conn.execute("INSERT INTO logs (time, customer, traffic, description, cost_loss) VALUES (?, ?, ?, ?, ?)",
                     (time.strftime("%H:%M:%S"), "GLOBAL_AGENT", avg_conf*100, desc, 100.0))
        conn.commit()
        
        step += 1
        time.sleep(1.5)

if __name__ == "__main__":
    run_loop() 