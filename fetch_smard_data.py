import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_session():
    """Returns a requests.Session with retry logic configured."""
    session = requests.Session()
    retry = Retry(
        total=5, # Obergrenze
        read=5, # Leseversuch der Daten
        connect=5, # Verbindungsaufbauversuche
        backoff_factor=1, # expotentiell wachsende Wartezeit 1 * 2^0, 1 * 2^1
        status_forcelist=[429, 500, 502, 503, 504], # HTTP Statuscodes 429: Too Many Requests (Limit der SMARD API). die anderen sind Serverfehler
        # 404 ist bewusst nicht drin, da eine falsche URL nicht nochmal versucht werden muss.
    )
    adapter = HTTPAdapter(max_retries=retry) # addaptiert die retry Regeln, damit die Session bei einem Fehler nicht abstürzt
    session.mount('http://', adapter) # immer wenn die URL mit http startet, nutze den Adapter
    session.mount('https://', adapter)  # immer wenn die URL mit https startet, nutze den Adapter
    return session

def fetch_smard_data(filter_id, start_idx=-4, end_idx=-1):
    """
    Fetches Day-Ahead Prices (DE/LU) from SMARD API.
    Market area: DE/LU
    Filter ID: 4169
    Region: DE
    Resolution: hour

    """
    session = get_session()

    base_url = "https://www.smard.de/app/chart_data"
    region = "DE"
    resolution = "hour"

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

    # We need data for the last 7 days and upcoming 24 hours.
    # The timestamps array contains milliseconds timestamps. Each represents a week or chunk of data.
    # We will fetch the last two chunks to ensure we cover the requested time window.

    recent_timestamps = timestamps[start_idx:end_idx]
    all_series = []

    for ts in recent_timestamps:
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

    return all_series
