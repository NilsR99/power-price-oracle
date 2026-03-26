import streamlit as st
import pandas as pd
import os

# Importiere unsere ausgelagerten Diagramm-Funktionen
import diagramme.korrelationsmatrix as km
import diagramme.hypothese_1 as h1
import diagramme.hypothese_2 as h2
import diagramme.standardlastprofil as slp

# --- 1. Streamlit Seitenkonfiguration ---
st.set_page_config(page_title="BIA Power Oracle", layout="wide")
st.title("⚡ Strommarkt Analyse")

# --- 2. Daten laden (mit Caching) ---
@st.cache_data
def load_data(file_path):
    # Achte auf den relativen Pfad mit Forward-Slashes!
    if not os.path.exists(file_path):
        return None
    df = pd.read_json(file_path, orient="records")
    df['date'] = pd.to_datetime(df['date'])
    return df

FILE_PATH = "data/merged/master_data_2026-03-26_13.json"
df_master = load_data(FILE_PATH)

if df_master is None:
    st.error(f"Daten nicht gefunden! Bitte prüfen Sie den Pfad: {FILE_PATH}")
    st.stop() # Bricht die Ausführung ab, wenn keine Daten da sind

# --- 3. Navigation (Das "Burger-Menü" in der Sidebar) ---
st.sidebar.title("Navigation")
menu_selection = st.sidebar.radio(
    "Wähle eine Analyse:",
    ("Korrelations-Matrix", "Hypothese 1 (Merit-Order)", "Hypothese 2 (Hitze)", "Tageslastprofil (SLP)")
)

st.sidebar.markdown("---") # Optischer Trenner in der Sidebar

# Vorab die numerischen Spalten extrahieren (wird oft gebraucht)
df_numeric = df_master.select_dtypes(include=['number'])

# --- 4. Routing Logik ---
# Abhängig von der Menüauswahl rufen wir die entsprechende Funktion aus diagramme.py auf
if menu_selection == "Korrelations-Matrix":
    km.render_korrelationsmatrix(df_master, df_numeric)

elif menu_selection == "Hypothese 1 (Merit-Order)":
    h1.render_hypothese_1(df_master)

elif menu_selection == "Hypothese 2 (Hitze)":
    h2.render_hypothese_2(df_master)

elif menu_selection == "Tageslastprofil (SLP)":
    slp.render_lastprofil(df_master)