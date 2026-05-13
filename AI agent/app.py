import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import numpy as np
import time

# --- TVINGA STREAMLIT ATT INTE CACHA DATA ---
st.cache_data.clear()

st.set_page_config(page_title="AI Agent Mission Control", layout="wide")

st.markdown("""<style>
    .main { background-color: #0e1117; }
    .status-card { padding: 15px; border-radius: 10px; border-left: 10px solid; margin-bottom: 15px; font-family: monospace; }
</style>""", unsafe_allow_html=True)

def get_latest_data():
    try:
        # Använd check_same_thread=False för att undvika SQLite-krockar med Streamlit
        conn = sqlite3.connect("live_data.db", check_same_thread=False)
        # Hämta den absolut senaste raden (rowid DESC)
        df = pd.read_sql("SELECT * FROM logs ORDER BY rowid DESC LIMIT 1", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

df = get_latest_data()

if not df.empty:
    row = df.iloc[0]
    konsensus_val = np.mean([row['rf_score'], row['lr_score'], row['gb_score']]) * 100
    is_rag_match = float(row['rag_score']) > 0.5
    is_attack = float(row['facit']) > 0.5
    timestamp = row['time']
    
    # --- DYNAMISK STATUS BANNER ---
    if is_attack and not is_rag_match:
        msg, color, desc = "⚠️ NYUPPTÄCKT ANOMALI: ML GISSAR", "#dbab09", "Okänt hotmönster. ML-modellerna detekterar avvikelse. Sparar till ChromaDB..."
    elif is_attack and is_rag_match:
        diag_name = row['description'].split(' | ')[0].replace('DIAGNOS: ', '')
        msg, color, desc = f"🎯 RAG-TRÄNAD: {diag_name}", "#f85149", "Vektormatchning bekräftad! Expertminnet spikar diagnosen."
    else:
        msg, color, desc = "✅ SYSTEM STATUS: NORMAL", "#3fb950", f"Trafikflödet är stabilt. Senaste analys: {timestamp}"

    st.markdown(f'<div class="status-card" style="background-color:{color}22; border-color:{color}; color:{color};"><h2>{msg}</h2><p style="color:white;">{desc}</p></div>', unsafe_allow_html=True)

    # --- VISUALISERING ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = konsensus_val,
            title = {'text': f"KONSENSUS @ {timestamp}"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "white"},
                'steps': [
                    {'range': [0, 40], 'color': "#3fb950"}, 
                    {'range': [40, 75], 'color': "#dbab09"}, 
                    {'range': [75, 100], 'color': "#f85149"}
                ],
                'threshold': {'line': {'color': "cyan", 'width': 6}, 'value': row['facit'] * 100}
            }
        ))
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
        st.plotly_chart(fig, width='stretch')

    with col_right:
        st.write("### Modell-reaktioner")
        for m, s in [("Random Forest", row['rf_score']), ("Log. Regression", row['lr_score']), ("Grad. Boosting", row['gb_score'])]:
            st.write(f"**{m}**")
            st.progress(float(s))
            st.caption(f"Score: {s*100:.1f}%")

    # --- RAG & DIAGNOS ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.write("### 🤖 RAG Status")
        if is_rag_match:
            st.success("MATCH FUNNEN")
            st.metric("Konfidens", "100%", delta="SPIKAD")
        else:
            st.info("Söker i expertminnet...")
            st.write("Ingen känd profil matchar nuvarande paketdata.")

    with c2:
        st.write("### 📋 Expert-diagnos & Åtgärd")
        st.code(row['description'].replace(' | ', '\n'), language="bash")

else:
    st.warning("Väntar på data från backend_agent.py... Kontrollera att agenten körs!")

# Auto-refresh var 1.2 sekund
time.sleep(1.2)
st.rerun()