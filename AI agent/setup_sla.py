import chromadb
# x
def setup_chroma():
    client = chromadb.PersistentClient(path="./chroma_db")
    # Skapa eller hämta kollektion för SLA
    collection = client.get_or_create_collection(name="customer_sla")

    customers = [f"Kund {chr(65+i)}" for i in range(10)]
    
    for i, name in enumerate(customers):
        # Vi lagrar kostnad_per_minut som metadata
        cost_per_min = (i + 1) * 150 # Olika avtal för olika kunder
        collection.upsert(
            documents=[f"SLA-avtal för {name}: Garanterad upptid 99.9%. Ersättning {cost_per_min} SEK/min."],
            metadatas=[{"customer": name, "cost_per_min": cost_per_min}],
            ids=[f"id_{i}"]
        )
    print("✅ ChromaDB populerad med SLA-avtal.")

if __name__ == "__main__":
    setup_chroma()