import chromadb
from sentence_transformers import SentenceTransformer
import os

# --- STEG 1: INITIALISERING ---
# Vi använder en persistent klient så att datan sparas på hårddisken i mappen ./chroma_db
client = chromadb.PersistentClient(path="./chroma_db")

# Vi skapar en kollektion (motsvarar en tabell) för våra nätverksincidenter
collection = client.get_or_create_collection(name="network_expert_knowledge")

# Vi laddar en Embedding-modell. Denna översätter text till vektorer (listor med siffror).
# Det är dessa vektorer som gör att AI:n kan förstå "betydelsen" av ett mönster.
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# --- STEG 2: DEFINIERA EXPERTKUNSKAP ---
# Här bevarar vi orsakerna (Causes) och kopplar dem till specifika Action Codes.
# Detta är hjärtat i RAG: att hämta rätt instruktion baserat på observation.
knowledge_base = [
    {
        "id": "dos_attack",
        "pattern": "Hög paketfrekvens (count), låg variationsgrad (diff_srv_rate), TCP protokoll",
        "cause": "SYN Flood / Denial of Service",
        "action_code": "BLOCK_IP_AND_RATE_LIMIT",
        "remediation": "Aktivera TCP Intercept och begränsa anslutningar per sekund från käll-IP."
    },
    {
        "id": "port_scan",
        "pattern": "Lång varaktighet, små paketmängder, diff_srv_rate indikerar spridning",
        "cause": "Nmap Port Scanning / Probing",
        "action_code": "ISOLATE_HOST",
        "remediation": "Flytta käll-IP till ett karantän-VLAN och flagga för manuell granskning."
    }
]

# --- STEG 3: POPULERA DATABASEN ---
for item in knowledge_base:
    # Vi skapar en embedding av själva 'mönstret'
    vector = embedder.encode(item["pattern"]).tolist()
    
    collection.add(
        embeddings=[vector],
        metadatas=[{
            "cause": item["cause"], 
            "action": item["action_code"], 
            "remediation": item["remediation"]
        }],
        ids=[item["id"]]
    )

print("✅ RAG: Vektordatabasen ChromaDB är nu laddad med expertinstruktioner.")