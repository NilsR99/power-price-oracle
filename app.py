import streamlit as st
import pandas as pd
import os
import glob
import datetime

from merge_script import run_merge_pipeline

# Importiere ausgelagerte Diagramm-Funktionen
import diagramme.korrelationsmatrix as km
import diagramme.hypothese_1 as h1
import diagramme.hypothese_2 as h2
import diagramme.standardlastprofil as slp
import diagramme.kreisdiagramm_Energiemix as kdem
import diagramme.heatmap_negative_preise as hnp

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

# --- UI: Die ETL-Steuerzentrale (Startseite / Sidebar) ---
st.sidebar.title("Daten-Manager")
st.sidebar.markdown("Generiere einen neuen Datensatz")

# Datums-Eingabefelder mit der harten 2020-2025 Grenze aus deiner Pipeline
col1, col2 = st.sidebar.columns(2)
with col1:
    ui_start_date = st.date_input(
        "Startdatum", 
        min_value=datetime.date(2020, 1, 1), 
        max_value=datetime.date(2025, 12, 31), 
        value=datetime.date(2025, 1, 1)
    )
with col2:
    ui_end_date = st.date_input(
        "Enddatum", 
        min_value=datetime.date(2020, 1, 1), 
        max_value=datetime.date(2025, 12, 31), 
        value=datetime.date(2025, 12, 31)
    )

# Der entkoppelte Action-Button
if st.sidebar.button("Daten live abrufen", use_container_width=True):
    # Sobald geklickt wird, zeigen wir einen Lade-Indikator
    with st.spinner(f"Lade API-Daten von {ui_start_date} bis {ui_end_date}..."):
        try:
            # Aufruf Pipeline!
            new_file_path = run_merge_pipeline(
                start_date=ui_start_date.strftime("%Y-%m-%d"), 
                end_date=ui_end_date.strftime("%Y-%m-%d")
            )
            if new_file_path:
             st.sidebar.success("Daten erfolgreich generiert!")
             st.cache_data.clear() # NEU: Zwingt Streamlit, die alte Datei zu vergessen
             st.rerun()
        except Exception as e:
            st.sidebar.error(f"Fehler beim Abruf: {e}")

st.sidebar.markdown("---")

FILE_PATH = get_latest_data_file()

if FILE_PATH is None:
    st.error("Keine Datengrundlage gefunden!")
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
st.markdown(f"**🗓️ Analysierter Zeitraum:** `{ui_start_date}` bis `{ui_end_date}` | **📊 Datenpunkte:** `{anzahl_stunden} Stunden`")
st.markdown("---") # Optische Trennlinie, bevor die eigentlichen Diagramme beginnen

# Wir reservieren diesen Bereich ganz oben in der Sidebar
sidebar_dynamic_filters = st.sidebar.container()

# --- Navigation (Das "Burger-Menü" in der Sidebar) ---
st.sidebar.title("Navigation")
menu_selection = st.sidebar.radio(
    "Wähle eine Analyse:",
    ("Energiemix", "Heatmap: Negative Preise", "Korrelations-Matrix", "Hypothese 1 (Merit-Order)", "Hypothese 2 (Hitze)", "Tageslastprofil (SLP)")
)

st.sidebar.markdown("---") # Optischer Trenner in der Sidebar

# Vorab die numerischen Spalten extrahieren (wird oft gebraucht)
df_numeric = df_master.select_dtypes(include=['number'])

# --- Routing Logik ---
# Abhängig von der Menüauswahl rufen wir die entsprechende Funktion aus diagramme.py auf
if menu_selection == "Energiemix":
    kdem.render_energiemix_pie(df_master, sidebar_dynamic_filters)

elif menu_selection == "Heatmap: Negative Preise":
    hnp.render_heatmap(df_master)

elif menu_selection == "Korrelations-Matrix":
    km.render_korrelationsmatrix(df_numeric, sidebar_dynamic_filters)

elif menu_selection == "Hypothese 1 (Merit-Order)":
    h1.render_hypothese_1(df_master)

elif menu_selection == "Hypothese 2 (Hitze)":
    h2.render_hypothese_2(df_master)

elif menu_selection == "Tageslastprofil (SLP)":
    slp.render_lastprofil(df_master, sidebar_dynamic_filters)