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

# --- 3. Dynamische Datenvorbereitung & UI-Filter ---
    # Nur numerische Spalten extrahieren
    df_numeric = df_master.select_dtypes(include=['number'])
    all_available_columns = df_numeric.columns.tolist()
    
    st.sidebar.header("⚙️ Analyse-Einstellungen")
    st.sidebar.markdown("Wähle die Variablen für die Korrelationsmatrix:")
    
    # Das Multiselect-Widget
    selected_columns = st.sidebar.multiselect(
        "Metriken auswählen",
        options=all_available_columns,
        default=None
    )

    # --- 4. Datenqualität & Fehlerabfang ---
    # Logik-Schutz: Eine Korrelation braucht mindestens 2 Variablen
    if len(selected_columns) < 2:
        st.error("⚠️ Analytischer Fehler: Du musst mindestens 2 Variablen auswählen, um eine Korrelation zu berechnen.")
    else:
        # Den Datensatz exakt auf die Auswahl des Nutzers zuschneiden
        df_filtered = df_numeric[selected_columns]
        
        # Missing Values für die AUSGEWÄHLTEN Spalten anzeigen
        missing_data_ratio = df_filtered.isna().sum() / len(df_filtered) * 100
        st.sidebar.markdown("---")
        st.sidebar.write("📉 **Datenlücken (NaN) der Auswahl:**")
        st.sidebar.dataframe(missing_data_ratio.round(2))

        # --- 5. Korrelationsmatrix berechnen & visualisieren ---
        st.subheader("Dynamische Korrelations-Heatmap (Pearson)")
        st.markdown("*Achtung: Ausgeblendete Variablen (z.B. Grundlast) können zu einer verzerrten Kausalitätswahrnehmung führen.*")

        # Matrix wird nur mit den ausgewählten Spalten berechnet
        corr_matrix = df_filtered.corr()

        fig = px.imshow(
            corr_matrix, 
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1
        )
        
        fig.update_layout(
            height=max(400, len(selected_columns) * 60), # Höhe wächst dynamisch mit der Anzahl der Variablen mit
            margin=dict(l=0, r=0, b=0, t=30)
        )

        st.plotly_chart(fig, use_container_width=True) 


# --- 6. Deep Dive: Nicht-lineare Scatter-Analyse ---
        st.markdown("---")
        st.subheader("🔬 Deep Dive: Temperatur vs. Preisstruktur")
        
        # Defensive Programmierung: Prüfen, ob die benötigten Spalten existieren
        required_cols = ["temperature_2m", "price_day_ahead"]
        missing_cols = [col for col in required_cols if col not in df_master.columns]
        
        if missing_cols:
            st.warning(f"⚠️ Für diesen Plot fehlen folgende Spalten im Datensatz: {missing_cols}")
        else:
            # Dynamische Farbgebung prüfen (Falls Winddaten da sind, nutzen wir sie)
            color_var = "wind_speed_120m" if "wind_speed_120m" in df_master.columns else None
            
            fig_scatter = px.scatter(
                df_master,
                x="temperature_2m",
                y="price_day_ahead",
                color=color_var,
                color_continuous_scale="Viridis", # Ein perceptuell uniformes Farbschema
                opacity=0.6, # Leicht transparent, um Überlappungen (Overplotting) sichtbar zu machen
                title="Day-Ahead-Preis-Dynamik (Eingefärbt nach Windgeschwindigkeit)",
                labels={
                    "temperature_2m": "Temperatur (°C)",
                    "price_day_ahead": "Day-Ahead Preis (€/MWh)",
                    "wind_speed_120m": "Windgeschw. 120m (m/s)"
                },
                hover_data=["date"] # Zeigt das genaue Datum an, wenn man mit der Maus über einen Punkt fährt
            )
            
            # Das Layout auf Lesbarkeit optimieren
            fig_scatter.update_layout(
                height=600,
                xaxis_title="Temperatur in °C",
                yaxis_title="Börsenstrompreis in €/MWh",
                plot_bgcolor="rgba(0,0,0,0)" # Macht den Hintergrund sauberer
            )
            
            # Eine Nulllinie für negative Strompreise einzeichnen
            fig_scatter.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="0 € Grenze")

            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Fachliche Interpretation für den Nutzer hinzufügen
            st.info("""
            **Analytische Beobachtung:** Achten Sie auf die Punkte *unterhalb* der roten gestrichelten Linie (negative Preise). 
            Treten diese eher bei bestimmten Temperaturen auf? Welche Farbe (Windgeschwindigkeit) dominiert bei den tiefsten Preisen? 
            Diese Grafik beweist, dass ein linearer Korrelationswert von -0,28 die physikalische Realität massiv unterschätzt.
            """)
        