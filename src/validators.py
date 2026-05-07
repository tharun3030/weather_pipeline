import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database import get_connection
import logging

# --- Valid ranges for weather data ---
VALID_RANGES = {
    'temperature_c':  (-90, 60),
    'humidity':       (0, 100),
    'pressure_hpa':   (870, 1085),
    'wind_speed_mps': (0, 115),
    'visibility_m':   (0, 100000),
}


def validate_record(data):
    """
    Validate a single weather record dictionary.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    # Check required fields exist
    required = ['city_name', 'country', 'temperature_c', 'humidity',
                'pressure_hpa', 'wind_speed_mps', 'weather_condition']
    for field in required:
        if data.get(field) is None:
            errors.append(f"Missing required field: {field}")

    # Check numeric ranges
    for field, (low, high) in VALID_RANGES.items():
        value = data.get(field)
        if value is not None:
            if not (low <= value <= high):
                errors.append(f"{field} out of range: {value} (expected {low}–{high})")

    # Check city name is a non-empty string
    if not isinstance(data.get('city_name', ''), str) or not data.get('city_name', '').strip():
        errors.append("city_name must be a non-empty string")

    # Check humidity is an integer
    humidity = data.get('humidity')
    if humidity is not None and not isinstance(humidity, int):
        errors.append(f"humidity should be integer, got {type(humidity).__name__}")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_batch(records):
    """
    Validate a list of weather records.
    Returns (valid_records, invalid_records) with error details.
    """
    print("\n📋 VALIDATING RECORDS...")
    valid   = []
    invalid = []

    for record in records:
        is_valid, errors = validate_record(record)
        if is_valid:
            valid.append(record)
            print(f"  ✅ {record.get('city_name')} — passed all checks")
        else:
            invalid.append({'record': record, 'errors': errors})
            print(f"  ❌ {record.get('city_name')} — {len(errors)} error(s):")
            for err in errors:
                print(f"       • {err}")

    print(f"\n  Valid: {len(valid)} | Invalid: {len(invalid)}\n")
    return valid, invalid


def check_database_quality():
    """
    Run quality checks directly on the database.
    Reports duplicates, nulls, and record counts.
    """
    print("\n🔍 DATABASE QUALITY REPORT")
    print("=" * 45)

    conn = get_connection()
    cursor = conn.cursor()

    # Total records
    cursor.execute("SELECT COUNT(*) FROM weather_records")
    total = cursor.fetchone()[0]
    print(f"  Total weather records : {total}")

    # Records per city
    cursor.execute('''
        SELECT c.city_name, COUNT(w.record_id) as count
        FROM cities c
        LEFT JOIN weather_records w ON c.city_id = w.city_id
        GROUP BY c.city_name
        ORDER BY count DESC
    ''')
    print("\n  Records per city:")
    for row in cursor.fetchall():
        print(f"    {row[0]:<15} {row[1]} record(s)")

    # Null check on critical columns
    print("\n  Null value check:")
    for col in ['temperature_c', 'humidity', 'pressure_hpa', 'wind_speed_mps']:
        cursor.execute(f"SELECT COUNT(*) FROM weather_records WHERE {col} IS NULL")
        nulls = cursor.fetchone()[0]
        status = "✅" if nulls == 0 else f"⚠️  {nulls} nulls"
        print(f"    {col:<20} {status}")

    # Duplicate check (same city, same timestamp)
    cursor.execute('''
        SELECT city_id, timestamp, COUNT(*) as cnt
        FROM weather_records
        GROUP BY city_id, timestamp
        HAVING cnt > 1
    ''')
    dupes = cursor.fetchall()
    print(f"\n  Duplicate records     : {'None ✅' if not dupes else len(dupes)}")

    # Temperature range sanity check
    cursor.execute('''
        SELECT c.city_name, w.temperature_c
        FROM weather_records w
        JOIN cities c ON w.city_id = c.city_id
        WHERE w.temperature_c < -90 OR w.temperature_c > 60
    ''')
    outliers = cursor.fetchall()
    print(f"  Temperature outliers  : {'None ✅' if not outliers else len(outliers)}")

    # Total alerts logged
    cursor.execute("SELECT COUNT(*) FROM alerts")
    alert_count = cursor.fetchone()[0]
    print(f"  Total alerts logged   : {alert_count}")

    print("=" * 45)
    conn.close()


if __name__ == "__main__":
    check_database_quality()