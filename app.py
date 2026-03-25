import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. Streamlit Seitenkonfiguration ---
st.set_page_config(page_title="BIA Power Oracle", layout="wide")
st.title("Strommarkt Analyse 2025")

# --- 2. Daten laden (mit Caching für Performance) ---
# Das @st.cache_data Dekorator verhindert, dass die große JSON bei 
# jedem Klick neu geladen wird.
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_json(file_path, orient="records")
    df['date'] = pd.to_datetime(df['date'])
    return df

# HIER DEN PFAD ZU IHRER AKTUELLSTEN MASTER-JSON EINTRAGEN:
# (Passen Sie den Dateinamen an den letzten Durchlauf Ihrer Pipeline an)
FILE_PATH = "data\merged\master_data_2026-03-25_18.json"

df_master = load_data(FILE_PATH)

if df_master is None:
    st.error(f"Daten nicht gefunden! Bitte prüfen Sie den Pfad: {FILE_PATH}")
else:
    st.success(f"Datensatz erfolgreich geladen: {len(df_master)} Stunden.")

    # --- 3. Datenvorbereitung für die Matrix ---
    # Wir filtern strikt nach numerischen Spalten, da Datetime-Strings 
    # die Korrelationsberechnung zum Absturz bringen.
    df_numeric = df_master.select_dtypes(include=['number'])
    
    # Kritischer Schritt: Behandlung von NaN-Werten vor der Korrelation
    # Wir lassen Pandas hier die paarweise Löschung vornehmen, loggen aber die Warnung
    missing_data_ratio = df_numeric.isna().sum() / len(df_numeric) * 100
    
    st.sidebar.header("Datenqualität")
    st.sidebar.write("Fehlende Werte (%):")
    st.sidebar.dataframe(missing_data_ratio.round(2))

    # --- 4. Korrelationsmatrix berechnen & visualisieren ---
    st.subheader("Korrelations-Heatmap (Pearson)")
    st.markdown("""
    *Hinweis: Zeigt lineare Zusammenhänge. Werte nahe 1 bedeuten starke positive, 
    Werte nahe -1 starke negative Korrelation. Der Day-Ahead-Preis verhält sich 
    zu erneuerbaren Energien oft nicht-linear!*
    """)

    # Berechnung der Matrix
    corr_matrix = df_numeric.corr()

    # Interaktiver Plotly-Plot anstelle eines statischen Bildes
    fig = px.imshow(
        corr_matrix, 
        text_auto=".2f", # Zeigt die Werte auf 2 Nachkommastellen genau
        aspect="auto",
        color_continuous_scale="RdBu_r", # Rot für Hitze (positiv), Blau für Kälte (negativ)
        zmin=-1, zmax=1
    )
    
    # Layout optimieren, damit die langen Spaltennamen lesbar bleiben
    fig.update_layout(
        height=700,
        margin=dict(l=0, r=0, b=0, t=30)
    )

    st.plotly_chart(fig, use_container_width=True)