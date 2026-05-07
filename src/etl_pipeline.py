import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.api_client import fetch_all_cities
from src.database import insert_city, insert_weather_record, insert_alert, get_all_cities
from config.config import CITIES, TEMP_HIGH_THRESHOLD, TEMP_LOW_THRESHOLD, HUMIDITY_HIGH_THRESHOLD, WIND_HIGH_THRESHOLD

def extract():
    """
    EXTRACT: Pull weather data from OpenWeatherMap for all configured cities.
    Returns raw list of weather dictionaries.
    """
    print("=" * 50)
    print("STEP 1: EXTRACT")
    print("=" * 50)
    results, failures = fetch_all_cities(CITIES)
    print(f"  Extracted {len(results)} records, {failures} failures.\n")
    return results


def transform(raw_data):
    """
    TRANSFORM: Clean, validate, and enrich the raw data.
    Returns a list of cleaned records ready for loading.
    """
    print("=" * 50)
    print("STEP 2: TRANSFORM")
    print("=" * 50)

    transformed = []
    skipped = 0

    for record in raw_data:
        # --- Validation: skip records with missing critical fields ---
        if record.get('temperature_c') is None:
            print(f"  ⚠️  Skipping {record.get('city_name')} — missing temperature.")
            skipped += 1
            continue

        if record.get('humidity') is None:
            print(f"  ⚠️  Skipping {record.get('city_name')} — missing humidity.")
            skipped += 1
            continue

        # --- Cleaning: round numeric fields ---
        record['temperature_c']  = round(record['temperature_c'], 2)
        record['feels_like_c']   = round(record['feels_like_c'], 2)
        record['temp_min_c']     = round(record['temp_min_c'], 2)
        record['temp_max_c']     = round(record['temp_max_c'], 2)
        record['wind_speed_mps'] = round(record['wind_speed_mps'], 2)

        # --- Enrichment: add heat index category ---
        temp = record['temperature_c']
        if temp >= 35:
            record['heat_category'] = 'Extreme'
        elif temp >= 28:
            record['heat_category'] = 'Hot'
        elif temp >= 20:
            record['heat_category'] = 'Warm'
        elif temp >= 10:
            record['heat_category'] = 'Mild'
        else:
            record['heat_category'] = 'Cold'

        transformed.append(record)
        print(f"  ✅ {record['city_name']}: {record['temperature_c']}°C "
              f"({record['heat_category']}) | {record['humidity']}% humidity")

    print(f"\n  Transformed {len(transformed)} records, skipped {skipped}.\n")
    return transformed


def check_alerts(city_id, record_id, data):
    """
    Check thresholds and log alerts to the database.
    """
    alerts_triggered = []

    if data['temperature_c'] > TEMP_HIGH_THRESHOLD:
        insert_alert(city_id, record_id, 'HIGH_TEMP', data['temperature_c'], TEMP_HIGH_THRESHOLD)
        alerts_triggered.append(f"🌡️  High temp: {data['temperature_c']}°C")

    if data['temperature_c'] < TEMP_LOW_THRESHOLD:
        insert_alert(city_id, record_id, 'LOW_TEMP', data['temperature_c'], TEMP_LOW_THRESHOLD)
        alerts_triggered.append(f"🥶 Low temp: {data['temperature_c']}°C")

    if data['humidity'] > HUMIDITY_HIGH_THRESHOLD:
        insert_alert(city_id, record_id, 'HIGH_HUMIDITY', data['humidity'], HUMIDITY_HIGH_THRESHOLD)
        alerts_triggered.append(f"💧 High humidity: {data['humidity']}%")

    if data['wind_speed_mps'] > WIND_HIGH_THRESHOLD:
        insert_alert(city_id, record_id, 'HIGH_WIND', data['wind_speed_mps'], WIND_HIGH_THRESHOLD)
        alerts_triggered.append(f"💨 High wind: {data['wind_speed_mps']} m/s")

    return alerts_triggered


def load(transformed_data):
    """
    LOAD: Insert transformed records into the SQLite database.
    Also checks alert thresholds for each record.
    """
    print("=" * 50)
    print("STEP 3: LOAD")
    print("=" * 50)

    loaded = 0
    total_alerts = []

    for data in transformed_data:
        try:
            # Insert city (or get existing city_id)
            city_id = insert_city(
                data['city_name'],
                data['country'],
                data['latitude'],
                data['longitude']
            )

            # Insert weather record
            record_id = insert_weather_record(city_id, data)

            # Check alerts
            alerts = check_alerts(city_id, record_id, data)
            total_alerts.extend([(data['city_name'], a) for a in alerts])

            loaded += 1
            print(f"  ✅ Loaded {data['city_name']} (record_id: {record_id})")

        except Exception as e:
            logging.error(f"Failed to load {data.get('city_name')}: {e}")
            print(f"  ❌ Failed to load {data.get('city_name')}: {e}")

    print(f"\n  Loaded {loaded} records into database.")

    if total_alerts:
        print(f"\n  ⚠️  {len(total_alerts)} alert(s) triggered:")
        for city, alert in total_alerts:
            print(f"     [{city}] {alert}")
    else:
        print("  ✅ No alerts triggered.")

    print()
    return loaded, total_alerts


def run_pipeline():
    """
    Run the full ETL pipeline: Extract → Transform → Validate → Load.
    """
    from src.validators import validate_batch

    print("\n" + "=" * 50)
    print("  WEATHER DATA PIPELINE — STARTING RUN")
    print("=" * 50 + "\n")

    raw_data    = extract()
    transformed = transform(raw_data)

    # Validate before loading
    valid_records, invalid_records = validate_batch(transformed)

    loaded, alerts = load(valid_records)

    print("=" * 50)
    print("  PIPELINE COMPLETE")
    print(f"  Records loaded  : {loaded}")
    print(f"  Records rejected: {len(invalid_records)}")
    print(f"  Alerts raised   : {len(alerts)}")
    print("=" * 50 + "\n")

    return loaded, alerts


if __name__ == "__main__":
    run_pipeline()