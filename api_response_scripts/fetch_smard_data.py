import requests
import logging
import pandas as pd
import os
from api_response_scripts.api_client import create_retry_session 

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_smard_data(filter_id, metric_name, start_date, end_date):
    """
    Fetches Data from SMARD API and exports it as an ISO-formatted JSON.
    """
    session = create_retry_session()
    base_url = "https://www.smard.de/app/chart_data"
    region = "DE"
    resolution = "hour"

    # 1. Ziel-Zeitraum in UTC datetime umwandeln
    start_dt = pd.to_datetime(start_date, utc=True)
    # Setze end_dt auf die letzte Sekunde des Jahres (31.12.2025 23:59:59)
    end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    # In Millisekunden für den Abgleich mit dem API-Index
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    # 1. Fetch available timestamps
    index_url = f"{base_url}/{filter_id}/{region}/index_{resolution}.json"
    logging.info(f"Fetching index from {index_url}")

    try:
        response = session.get(index_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        timestamps = data.get('timestamps', [])
        if not timestamps:
            logging.error("No timestamps found in the index.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching index: {e}")
        return None

    # Chunks filtern (Die Logik-Korrektur)
    # Ein Chunk ist ca. 1 Woche lang (7 Tage * 24h * 60m * 60s * 1000ms = 604.800.000 ms)
    # Wir nehmen alle Chunks, die enden, nachdem unser Zeitraum beginnt, 
    # UND die beginnen, bevor unser Zeitraum endet.
    chunk_duration_ms = 7 * 24 * 60 * 60 * 1000
    target_timestamps = [
        ts for ts in timestamps 
        if (ts + chunk_duration_ms) >= start_ms and ts <= end_ms
    ]

    logging.info(f"Lade {len(target_timestamps)} Wochen-Pakete für das Jahr {start_date[:4]}...")
    all_series = []

    for ts in target_timestamps:
        data_url = f"{base_url}/{filter_id}/{region}/{filter_id}_{region}_{resolution}_{ts}.json"
        logging.info(f"Fetching data from {data_url}")
        try:
            res = session.get(data_url, timeout=10)
            res.raise_for_status()
            chunk_data = res.json()
            series = chunk_data.get('series', [])
            all_series.extend(series)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data for timestamp {ts}: {e}")
            continue

    if not all_series:
        logging.error("No data fetched from the API.")
        return None

    # --- Transformation in das Ziel-Format ---
    
    # Rohe Liste in einen Pandas DataFrame wandeln
    df = pd.DataFrame(all_series, columns=["timestamp_ms", metric_name])
    
    # Millisekunden in korrektes UTC-Datum konvertieren
    df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    
    # Duplikate entfernen (Chunks bei SMARD überschneiden sich oft am Rand)
    df = df.drop_duplicates(subset=["date"]).sort_values("date")

    # Daten ausßerhalb des Zeitraums abschneiden!
    mask = (df["date"] >= start_dt) & (df["date"] <= end_dt)
    df = df.loc[mask].reset_index(drop=True)
    
    # Nicht mehr benötigte Millisekunden-Spalte löschen
    df = df.drop(columns=["timestamp_ms"])
    
    # Spalten in die richtige Reihenfolge bringen
    df = df[["date", metric_name]]
    
    # --- 3. Export als JSON ---
    os.makedirs("data/smard", exist_ok=True)
    json_path = f"data/smard/smard_{metric_name}_{filter_id}.json"
    
    # orient="records" und date_format="iso" erzeugt exakt das gewünschte Format
    df.to_json(json_path, orient="records", date_format="iso", indent=4)
    logging.info(f"Erfolgreich gespeichert: {json_path}")
    
    return json_path
