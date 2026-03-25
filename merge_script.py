import pandas as pd
from datetime import datetime
import os
import logging

# Importiere die Hauptfunktionen aus deinen bestehenden Dateien
# (Passe die Dateinamen 'fetch_weather' und 'smard_api' an deine tatsächlichen Dateinamen an)
from fetch_weather_data import fetch_weather_data
from fetch_smard_data import fetch_smard_data

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- ZENTRALE KONFIGURATION ---
JAHR = "2025"
START_DATE = f"{JAHR}-01-01"
END_DATE = f"{JAHR}-12-31"
# Liste der SMARD-IDs (Filter-ID, Gewünschter_Spaltenname)
SMARD_CONFIG = [
    ("4169", "price_day_ahead"),      # Target: Der Börsenpreis
    ("410",  "actual_total_load"),    # Realisierter Stromverbrauch (Gesamtlast)
    ("4359", "actual_residual_load"), # Ist-Residuallast (Gesamtlast minus Erneuerbare)
    ("4067", "actual_wind_onshore"),  # Ist-Erzeugung Wind Onshore
    ("4068", "actual_pv"),            # Ist-Erzeugung Photovoltaik
    ("1225", "actual_wind_offshore"), # Ist-Erzeugung Wind Offshore (extrem wichtig!)
    ("4071", "actual_gas"),           # Ist-Erzeugung Erdgas (oft das preissetzende Kraftwerk)
    ("1223", "actual_brown_coal")     # Ist-Erzeugung Braunkohle (Grundlast)
]
# ------------------------------

def run_merge_pipeline():
    logging.info(f"Starte Daten-Pipeline: Wetter und SMARD für den Zeitraum {START_DATE} - {END_DATE}")
    df_smard = None

    # 1. Daten abrufen (führt deine beiden Skripte aus)
    # Ich gehe davon aus, dass wir SMARD ID 4169 (Day-Ahead-Preis) abfragen
    logging.info("Lade Wetterdaten...")
    df_weather = fetch_weather_data(START_DATE, END_DATE)  # Angenommen, diese Funktion gibt einen DataFrame zurück
    df_weather['date'] = pd.to_datetime(df_weather['date'], utc=True)
    
    logging.info("Lade SMARD-Daten...")
    for filter_id, metric_name in SMARD_CONFIG:
        logging.info(f"--> Verarbeite SMARD ID {filter_id} (Spalte: '{metric_name}')...")
        
        # Sauberer Aufruf mit Keyword-Argumenten (verhindert Parameter-Dreher)
        smard_path = fetch_smard_data(
            filter_id=filter_id, 
            start_date=START_DATE, 
            end_date=END_DATE, 
            metric_name=metric_name
        )

        # Kritisches Error-Handling: Nur mergen, wenn Daten geliefert wurden
        if smard_path is None:
            logging.warning(f"Fehlende Daten für ID {filter_id}. Spalte '{metric_name}' wird im Master-Datensatz fehlen.")
            continue # Springt zur nächsten ID in der Schleife, anstatt abzustürzen!

        # Temporären DataFrame für die aktuelle Metrik erstellen
        df_temp = pd.read_json(smard_path, orient="records")
        df_temp['date'] = pd.to_datetime(df_temp['date'], utc=True)

        if df_smard is None:
            # Beim ersten Durchlauf: Die erste Tabelle wird zum Master (kein Merge nötig)
            df_smard = df_temp.copy()
        else:
            # Ab dem zweiten Durchlauf: Die neue Tabelle wird per Outer-Join angeflanscht
            df_smard = pd.merge(df_smard, df_temp, on='date', how='outer')

    # --- Bereinigung & Qualitätskontrolle ---
    logging.info("Führe finale chronologische Sortierung durch...")
    # Durch Outer Joins können Zeitstempel durcheinander geraten, Sortierung ist Pflicht
    df_smard = df_smard.sort_values('date').reset_index(drop=True)
    
    if df_smard is None or df_weather is None:
        logging.error("Pipeline abgebrochen: Eine der Datenquellen hat keine Daten geliefert.")
        return

    # 3. Der Merge (Outer Join)
    logging.info("Führe Daten anhand des Zeitstempels zusammen...")
    df_merged = pd.merge(df_weather, df_smard, on='date', how='outer')

    # Chronologisch sortieren, um ein sauberes Zeitreihen-Format zu garantieren
    df_merged = df_merged.sort_values('date').reset_index(drop=True)

    # 4. Export mit dynamischem Zeitstempel
    # Generiert das Format: YYYY-MM-DD_HH (z.B. 2026-03-25_13)
    current_time_str = datetime.now().strftime("%Y-%m-%d_%H")
    
    os.makedirs("data/merged", exist_ok=True)
    final_json_path = f"data/merged/master_data_{current_time_str}.json"

    # Exportieren der zusammengeführten Daten
    df_merged.to_json(final_json_path, orient="records", date_format="iso", indent=4)
    
    logging.info(f"Pipeline erfolgreich abgeschlossen! Datei gespeichert unter: {final_json_path}")

if __name__ == "__main__":
    run_merge_pipeline()