import pandas as pd
import os
import logging
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_entsoe_data(start_date, end_date, country_code="DE_LU"):
    """
    Ruft tatsächliche Erzeugungsdaten (Actual Generation) von ENTSO-E ab,
    flacht die Datenstruktur ab und exportiert eine ISO-formatierte JSON.
    """
    # 1. API-Key sicher aus der .env Datei laden
    load_dotenv()
    api_key = os.getenv('ENTSOE_API_KEY')
    
    if not api_key:
        logging.error("FATAL: Kein ENTSOE_API_KEY gefunden. Bitte in der .env Datei anlegen.")
        return None

    client = EntsoePandasClient(api_key=api_key)

    # 2. Zeitraum in timezone-aware Pandas Timestamps umwandeln (ENTSO-E Pflicht)
    start_dt = pd.Timestamp(start_date, tz='UTC')
    # +1 Tag und -1 Sekunde für das exakte Ende, wie beim SMARD Skript
    end_dt = pd.Timestamp(end_date, tz='UTC') + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    logging.info(f"Lade ENTSO-E Erzeugungsdaten für {country_code} von {start_dt.date()} bis {end_dt.date()}...")

    try:
        # Abruf der tatsächlichen Erzeugung (Actual Generation per Production Type)
        df = client.query_generation(country_code, start=start_dt, end=end_dt)
    except Exception as e:
        logging.error(f"API Fehler bei ENTSO-E: {e}")
        return None

    if df.empty:
        logging.warning("Die API hat keine Daten für diesen Zeitraum zurückgegeben.")
        return None

    # --- 3. Transformation in das Master-Format ---
    
    # Kritisches Problem lösen: ENTSO-E liefert einen MultiIndex (z.B. "Fossil Gas" -> "Actual Aggregated").
    # Für eine flache JSON (und unser Machine Learning Modell) müssen wir das eindimensional machen.
    # Wir machen aus ('Fossil Gas', 'Actual Aggregated') -> 'entsoe_fossil_gas'
    new_columns = []
    for col in df.columns:
        if isinstance(col, tuple):
            name = str(col[0]).replace(' ', '_').lower()
        else:
            name = str(col).replace(' ', '_').lower()
        new_columns.append(f"entsoe_{name}")
    
    df.columns = new_columns

    # Den Index (der die Zeitstempel enthält) zu einer normalen Spalte 'date' machen
    df = df.reset_index(names='date')
    
    # Sicherheitshalber auf reines UTC zwingen, damit der Merge mit Wetter & SMARD zu 100% klappt
    df['date'] = pd.to_datetime(df['date'], utc=True)
    
    # --- 4. Export als JSON ---
    os.makedirs("data/entsoe", exist_ok=True)
    json_path = f"data/entsoe/entsoe_generation_{country_code}_{start_date[:4]}.json"
    
    # orient="records" und date_format="iso" erzeugt exakt das SMARD-Format
    df.to_json(json_path, orient="records", date_format="iso", indent=4)
    logging.info(f"Erfolgreich gespeichert ({len(df)} Zeilen): {json_path}")
    
    return json_path

def main():
    # Beispielaufruf
    fetch_entsoe_data("2025-01-01", "2025-12-31")

if __name__ == "__main__":
    main()