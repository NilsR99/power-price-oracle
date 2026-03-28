import pandas as pd
from datetime import datetime
import os
import logging

from api_response_scripts.fetch_weather_data import fetch_weather_data
from api_response_scripts.fetch_smard_data import fetch_smard_data

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- ZENTRALE KONFIGURATION ---
# Liste der SMARD-IDs (Filter-ID, Gewünschter_Spaltenname)
SMARD_CONFIG = [
    ("4169", "price_day_ahead"),            # Target: Der Börsenpreis
    ("410",  "actual_total_load"),          # Realisierter Stromverbrauch (Gesamtlast)
    ("4359", "actual_residual_load"),       # Ist-Residuallast
    ("4067", "actual_wind_onshore"),        # Ist-Erzeugung Wind Onshore
    ("4068", "actual_pv"),                  # Ist-Erzeugung Photovoltaik
    ("1225", "actual_wind_offshore"),       # Ist-Erzeugung Wind Offshore
    ("4071", "actual_gas"),                 # Ist-Erzeugung Erdgas
    ("1223", "actual_brown_coal"),          # Ist-Erzeugung Braunkohle
    ("1224", "actual_nuclear"),             # Ist-Erzeugung Kernenergie
    ("1226", "actual_hydro"),               # Ist-Erzeugung Wasserkraft
    ("1227", "actual_other_conventional"),  # Ist-Erzeugung sonstige konventionelle Energieträger
    ("1228", "actual_other_renewables"),    # Ist-Erzeugung sonstige erneuerbare Energien
    ("4066", "actual_biomass"),             # Ist-Erzeugung Biomasse
    ("4069", "actual_hard_coal"),           # Ist-Erzeugung Steinkohle
    ("4070", "actual_pumped_storage")       # Ist-Erzeugung Pumpspeicher
]
# ------------------------------

def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    TESTBARE LOGIK: Prüft, ob die Eingabedaten im erlaubten Bereich (2020-2025) liegen
    und chronologisch Sinn machen.
    """
    min_date = pd.to_datetime("2010-01-01")
    max_date = pd.to_datetime("2025-12-31")

    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
    except Exception:
        raise ValueError("Ungültiges Datumsformat. Bitte YYYY-MM-DD verwenden.")

    if start_dt > end_dt:
        raise ValueError("Logischer Fehler: Das Startdatum darf nicht nach dem Enddatum liegen.")

    if start_dt < min_date or end_dt > max_date:
        raise ValueError("Die gewählten Daten liegen außerhalb des erlaubten Bereichs (01.01.2010 bis 31.12.2025).")

    return True

def process_smard_files(smard_paths: list) -> pd.DataFrame:
    """
    TESTBARE LOGIK: Nimmt eine Liste von Dateipfaden, lädt sie und merged sie.
    Isoliert die Pandas-Logik vom API-Abruf.
    """
    df_smard = None
    
    for smard_path in smard_paths:
        if smard_path is None or not os.path.exists(smard_path):
            continue

        df_temp = pd.read_json(smard_path, orient="records")
        df_temp['date'] = pd.to_datetime(df_temp['date'], utc=True)

        if df_smard is None:
            df_smard = df_temp.copy()
        else:
            df_smard = pd.merge(df_smard, df_temp, on='date', how='outer')

    if df_smard is not None:
        df_smard = df_smard.sort_values('date').reset_index(drop=True)

    return df_smard

def combine_master_data(df_weather: pd.DataFrame, df_smard: pd.DataFrame) -> pd.DataFrame:
    """
    TESTBARE LOGIK: Führt Wetter- und SMARD-DataFrames zusammen.
    Dies ist der kritischste mathematische Schritt und nun isoliert testbar.
    """
    if df_weather is None or df_weather.empty:
        raise ValueError("Kritischer Fehler: Wetterdaten fehlen oder sind leer.")
    if df_smard is None or df_smard.empty:
        raise ValueError("Kritischer Fehler: SMARD-Daten fehlen oder sind leer.")

    # Sicherstellen, dass beide Datensätze striktes UTC verwenden
    df_weather['date'] = pd.to_datetime(df_weather['date'], utc=True)
    df_smard['date'] = pd.to_datetime(df_smard['date'], utc=True)

    df_merged = pd.merge(df_weather, df_smard, on='date', how='outer')
    df_merged = df_merged.sort_values('date').reset_index(drop=True)

    return df_merged

def run_merge_pipeline(start_date: str, end_date: str):
    """
    DER ORCHESTRATOR: Steuert den Ablauf. 
    Liest jetzt Parameter dynamisch ein und verknüpft die testbaren Bausteine.
    """
    # 1. Strikte Validierung der Eingabedaten
    validate_date_range(start_date, end_date)
    
    logging.info(f"Starte Daten-Pipeline: Wetter und SMARD für den Zeitraum {start_date} bis {end_date}")

    # 2. Datenbeschaffung (APIs)
    logging.info("Lade Wetterdaten...")
    df_weather = fetch_weather_data(start_date, end_date) 

    logging.info("Lade SMARD-Daten...")
    valid_smard_paths = []
    for filter_id, metric_name in SMARD_CONFIG:
        logging.info(f"--> Verarbeite SMARD ID {filter_id} (Spalte: '{metric_name}')...")
        smard_path = fetch_smard_data(
            filter_id=filter_id, 
            start_date=start_date, 
            end_date=end_date, 
            metric_name=metric_name
        )
        if smard_path is None:
            logging.warning(f"Fehlende Daten für ID {filter_id}. Spalte '{metric_name}' wird fehlen.")
        else:
            valid_smard_paths.append(smard_path)

    # 3. Datenverarbeitung (Aufruf der testbaren Logik)
    df_smard = process_smard_files(valid_smard_paths)
    
    if df_smard is None:
        logging.error("Pipeline abgebrochen: Keine validen SMARD-Daten vorhanden.")
        return None

    logging.info("Führe finale Zusammenführung anhand des Zeitstempels durch...")
    df_merged = combine_master_data(df_weather, df_smard)

    # 4. Export
    current_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("data/merged", exist_ok=True)
    final_json_path = f"data/merged/master_data_{current_time_str}.json"

    df_merged.to_json(final_json_path, orient="records", date_format="iso", indent=4)
    logging.info(f"Pipeline erfolgreich abgeschlossen! Datei gespeichert unter: {final_json_path}")
    
    return final_json_path

if __name__ == "__main__":
    # Standardausführung (kann jetzt flexibel aufgerufen werden)
    run_merge_pipeline("2025-01-01", "2025-12-31")