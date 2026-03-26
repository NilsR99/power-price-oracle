import streamlit as st
import pandas as pd
import os
import glob

# Importiere unsere ausgelagerten Diagramm-Funktionen
import diagramme.korrelationsmatrix as km
import diagramme.hypothese_1 as h1
import diagramme.hypothese_2 as h2
import diagramme.standardlastprofil as slp

# --- Streamlit Seitenkonfiguration ---
st.set_page_config(page_title="BIA Power Oracle", layout="wide")
st.title("⚡ Strommarkt Analyse")

# --- Dynamische Datenfindung (Auto-Discovery) ---
def get_latest_data_file(directory="data/merged"):
    """Sucht automatisch die neueste JSON-Datei im angegebenen Verzeichnis."""
    if not os.path.exists(directory):
        return None
    
    # Finde alle JSON-Dateien im Ordner
    list_of_files = glob.glob(os.path.join(directory, "*.json"))
    
    if not list_of_files:
        return None
        
    # Nimm die Datei, die als letztes modifiziert/erstellt wurde
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

# --- Daten laden (mit Caching) ---
@st.cache_data
def load_data(file_path):
    df = pd.read_json(file_path, orient="records")
    df['date'] = pd.to_datetime(df['date'])
    return df

FILE_PATH = get_latest_data_file()

if FILE_PATH is None:
    st.error("⚠️ Keine Datengrundlage gefunden!")
    st.info("Bitte führe zuerst das ETL-Skript (z.B. `merge_pipeline.py`) aus, um die Wetter- und Strommarktdaten herunterzuladen. Das Dashboard erwartet die Daten im Ordner `data/merged/`.")
    st.stop() # Bricht die Ausführung hier sauber ab, ohne hässliche Fehlermeldungen zu werfen

# Daten laden und Erfolg melden
df_master = load_data(FILE_PATH)
st.sidebar.success(f"Daten geladen: {os.path.basename(FILE_PATH)}")

if df_master is None:
    st.error(f"Daten nicht gefunden! Bitte prüfen Sie den Pfad: {FILE_PATH}")
    st.stop() # Bricht die Ausführung ab, wenn keine Daten da sind

# --- Dynamische Zeitraum-Ermittlung und Anzeige ---
# Wir suchen den kleinsten und größten Zeitstempel im Datensatz
start_date = df_master['date'].min().strftime('%d.%m.%Y')
end_date = df_master['date'].max().strftime('%d.%m.%Y')
anzahl_stunden = len(df_master)

# Anzeige direkt unter dem Haupttitel auf der Startseite
st.markdown(f"**🗓️ Analysierter Zeitraum:** `{start_date}` bis `{end_date}` | **📊 Datenpunkte:** `{anzahl_stunden} Stunden`")
st.markdown("---") # Optische Trennlinie, bevor die eigentlichen Diagramme beginnen

# --- Navigation (Das "Burger-Menü" in der Sidebar) ---
st.sidebar.title("Navigation")
menu_selection = st.sidebar.radio(
    "Wähle eine Analyse:",
    ("Korrelations-Matrix", "Hypothese 1 (Merit-Order)", "Hypothese 2 (Hitze)", "Tageslastprofil (SLP)")
)

st.sidebar.markdown("---") # Optischer Trenner in der Sidebar

# Vorab die numerischen Spalten extrahieren (wird oft gebraucht)
df_numeric = df_master.select_dtypes(include=['number'])

# --- Routing Logik ---
# Abhängig von der Menüauswahl rufen wir die entsprechende Funktion aus diagramme.py auf
if menu_selection == "Korrelations-Matrix":
    km.render_korrelationsmatrix(df_master, df_numeric)

elif menu_selection == "Hypothese 1 (Merit-Order)":
    h1.render_hypothese_1(df_master)

elif menu_selection == "Hypothese 2 (Hitze)":
    h2.render_hypothese_2(df_master)

elif menu_selection == "Tageslastprofil (SLP)":
    slp.render_lastprofil(df_master)