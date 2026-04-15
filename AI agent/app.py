# Förklaring: Din frontend. Den läser från samma SQLite-fil som backend och ger användaren kontroll över systemet.
# En Jupyter-cell som kör en while True-loop "låser" hela programmet
# så du inte kan göra något annat
# Genom att köra backend.py och app.py separat 
# kan de kommunicera via databasen utan att krocka.

import streamlit as st
import sqlite3, pd
import plotly.express as px

st.title("🛡️ AI Cyber-Finance Dashboard")

conn = sqlite3.connect("live_data.db")

# Kill Switch Logik
if st.button("TOGGLE KILL SWITCH"):
    val = conn.execute("SELECT val FROM settings").fetchone()[0]
    conn.execute(f"UPDATE settings SET val = {0 if val==1 else 1}")
    conn.commit()

# Visa data
df = pd.read_sql("SELECT * FROM logs ORDER BY time DESC LIMIT 60", conn)
cost = pd.read_sql("SELECT total FROM finance", conn).iloc[0,0]

st.metric("Total SLA Penalty", f"{cost:,.0f} SEK")
st.plotly_chart(px.line(df, x='time', y='traffic', title="Live Network Traffic"))
st.table(df.head(5))