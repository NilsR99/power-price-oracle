import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_session():
    """Returns a requests.Session with retry logic configured."""
    session = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def fetch_smard_data():
    """
    Fetches Day-Ahead Prices (DE/LU) from SMARD API.
    Market area: DE/LU
    Filter ID: 4169
    Region: DE
    Resolution: hour

    API Base URL: https://www.smard.de/papi/v1/market-data/
    """
    session = get_session()

    # Base URL.
    # Note: the prompt requested "https://www.smard.de/papi/v1/market-data/" but that
    # endpoint returns 404. We use the actually functional endpoint for json market data.
    # We will use "https://www.smard.de/app/chart_data" to get actual data.
    base_url = "https://www.smard.de/app/chart_data"
    filter_id = "4169"
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

    recent_timestamps = timestamps[-2:]
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



def process_data(raw_data):
    """
    Processes the raw API data.
    - Converts Unix timestamps (milliseconds) to ISO-8601 UTC.
    - Ensures prices are correctly scaled (float).
    - Filters data for the last 7 days and upcoming 24 hours.
    """
    if not raw_data:
        return None

    df = pd.DataFrame(raw_data, columns=['timestamp', 'price_eur_mwh'])

    # Drop rows where price is null if any
    df = df.dropna(subset=['price_eur_mwh'])

    # Convert timestamps (ms) to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

    # Format to ISO-8601
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Convert back to datetime for filtering logic
    df['dt'] = pd.to_datetime(df['timestamp'], utc=True)

    # Define time window
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=7)
    end_time = now + timedelta(hours=24)

    # Filter
    mask = (df['dt'] >= start_time) & (df['dt'] <= end_time)
    filtered_df = df.loc[mask].copy()

    # Drop temp column
    filtered_df = filtered_df.drop(columns=['dt'])

    # Sort just in case
    filtered_df = filtered_df.sort_values(by='timestamp').reset_index(drop=True)

    return filtered_df


def export_data(df, directory='data', filename='day_ahead_prices.csv'):
    """
    Exports the DataFrame to a CSV file in the specified directory.
    """
    if df is None or df.empty:
        logging.warning("No data to export.")
        return

    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)

    df.to_csv(filepath, index=False)
    logging.info(f"Data exported successfully to {filepath}")
    return filepath


def generate_readme_insights(df):
    """
    Generates a Market Data Insights section for the README.
    Calculates statistics and adds a brief interpretation.
    """
    if df is None or df.empty:
        return ""

    mean_price = df['price_eur_mwh'].mean()
    min_price = df['price_eur_mwh'].min()
    max_price = df['price_eur_mwh'].max()
    std_dev = df['price_eur_mwh'].std()

    # Simple interpretation logic
    if std_dev > 40:
        volatility = "high volatility"
    elif std_dev > 20:
        volatility = "moderate volatility"
    else:
        volatility = "low volatility"

    if mean_price > 100:
        price_level = "relatively high"
    elif mean_price > 50:
        price_level = "moderate"
    else:
        price_level = "relatively low"

    insights = f"""## Market Data Insights

### What are "Day-Ahead Prices"?
The Day-Ahead price represents the auction-based clearing price for electricity delivery on the following day. Participants in the wholesale electricity market bid and offer electricity for each hour (or 15-minute intervals) of the next day. The intersection of the aggregated supply and demand curves determines the clearing price.

### Significance for Industrial Procurement
For industrial consumers, the Day-Ahead price is a critical benchmark. Procuring electricity strategically involves analyzing the spread between peak (times of high demand, e.g., morning and evening) and off-peak (times of low demand, e.g., night and weekend) prices. Industries can reduce costs by shifting energy-intensive processes to off-peak hours when prices are lower or even negative due to high renewable energy feed-in.

### Current Market Trend
Based on the retrieved data for the last 7 days and upcoming 24 hours:
- **Average Price**: €{mean_price:.2f}/MWh
- **Minimum Price**: €{min_price:.2f}/MWh
- **Maximum Price**: €{max_price:.2f}/MWh
- **Standard Deviation**: €{std_dev:.2f}/MWh

**Interpretation**: The current market exhibits a **{price_level}** price level with **{volatility}**. The spread between the minimum and maximum price is €{(max_price - min_price):.2f}/MWh, which highlights the potential savings from load shifting and flexible industrial production.
"""
    return insights


def update_readme(insights_text, readme_path='README.md'):
    """
    Updates the README.md file with the newly generated insights.
    Replaces the existing '## Market Data Insights' section or appends it to the end.
    """
    if not os.path.exists(readme_path):
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("# SMARD Electricity Market Data\n\n")

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    start_marker = "## Market Data Insights"

    if start_marker in content:
        # Assuming the section goes until the end of the file or the next H1/H2 (we'll just replace everything from the marker)
        # For simplicity, we split and replace everything from the marker to the end of the file.
        # This assumes "Market Data Insights" is the last section.
        parts = content.split(start_marker)
        pre_content = parts[0]

        # If there are subsequent sections, find the next H1/H2
        post_content = parts[1]
        next_section_idx = -1

        lines = post_content.split('\n')
        for i, line in enumerate(lines[1:]): # skip the first line which is just the marker text
            if line.startswith('# ') or line.startswith('## '):
                next_section_idx = i + 1
                break

        if next_section_idx != -1:
            post_content = '\n'.join(lines[next_section_idx:])
            new_content = pre_content + insights_text + '\n' + post_content
        else:
            new_content = pre_content + insights_text + '\n'
    else:
        new_content = content.rstrip() + '\n\n' + insights_text + '\n'

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    logging.info(f"Updated {readme_path} with new market data insights.")


def main():
    raw_data = fetch_smard_data()
    if raw_data:
        df = process_data(raw_data)
        if df is not None:
            export_data(df)
            insights = generate_readme_insights(df)
            update_readme(insights)
        else:
            logging.error("Failed to process data.")
    else:
        logging.error("Failed to fetch data from API.")

if __name__ == '__main__':
    main()
