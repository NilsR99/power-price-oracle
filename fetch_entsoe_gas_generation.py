import argparse
import json
import os
import pandas as pd
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

def main():
    parser = argparse.ArgumentParser(description="Fetch 'Fossil Gas' actual generation for DE_LU.")
    parser.add_argument("year", type=int, help="Year to fetch the data for (e.g. 2024)")
    args = parser.parse_args()

    year = args.year

    # Load environment variables from .env file
    load_dotenv()

    api_key = os.environ.get("ENTSOE_API_KEY")
    if not api_key:
        raise ValueError("ENTSOE_API_KEY not found in environment or .env file.")

    client = EntsoePandasClient(api_key=api_key)

    # Define parameters
    country_code = 'DE_LU'
    # Use timezone Europe/Berlin
    tz = "Europe/Berlin"
    start = pd.Timestamp(f"{year}-01-01", tz=tz)
    end = pd.Timestamp(f"{year+1}-01-01", tz=tz)

    print(f"Fetching generation data for {country_code} in {year}...")

    try:
        df = client.query_generation(country_code, start=start, end=end)
    except Exception as e:
        print(f"Error fetching data from ENTSO-E: {e}")
        return

    # Check if we got a Series or a DataFrame
    if isinstance(df, pd.Series):
        df = df.to_frame()

    # Find the column for 'Fossil Gas'
    # The columns might be a MultiIndex (e.g., ('Fossil Gas', 'Actual Aggregated'))
    # or flat string columns depending on the returned DataFrame
    gas_cols = []

    if isinstance(df.columns, pd.MultiIndex):
        # We find columns where the top level is "Fossil Gas"
        for col in df.columns:
            if 'Fossil Gas' in col:
                gas_cols.append(col)
    else:
        for col in df.columns:
            if 'Fossil Gas' == col:
                gas_cols.append(col)

    if not gas_cols:
        raise ValueError(f"Could not find 'Fossil Gas' in the generation data. Available columns: {list(df.columns)}")

    # Extract Fossil gas column(s)
    gas_series = df[gas_cols]

    # Sometimes it can be a DataFrame if there are multiple sub-levels matching
    # e.g., 'Fossil Gas' + 'Actual Aggregated' and 'Fossil Gas' + 'Actual Consumption'
    # If it is a DataFrame, sum it up (this aggregates across the selected columns)
    if isinstance(gas_series, pd.DataFrame):
        # Usually it's just 'Actual Aggregated', but sum is safe if there are multiple parts
        gas_series = gas_series.sum(axis=1)

    # Reset index to turn the DatetimeIndex into a column
    gas_df = gas_series.reset_index()
    # The first column is the timestamp (usually 'index' or similar), the second is the value
    gas_df.columns = ["date", "fossil_gas_generation"]

    # Ensure timezone is correct (entsoe-py often returns UTC or the requested tz)
    # Then format as ISO 8601
    gas_df["date"] = gas_df["date"].dt.tz_convert(tz).apply(lambda x: x.isoformat())

    # Output file name dynamically based on year
    output_filename = f"fossil_gas_generation_DE_LU_{year}.json"

    # Convert to JSON with orient='records'
    records = gas_df.to_dict(orient="records")

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4)

    print(f"Successfully saved {len(records)} records to {output_filename}")

if __name__ == "__main__":
    main()
