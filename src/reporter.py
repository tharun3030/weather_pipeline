import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database import get_connection
from config.config import REPORT_DIR
from datetime import datetime


def get_latest_snapshot():
    """Get the most recent weather record for each city."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.city_name, c.country,
               w.temperature_c, w.feels_like_c, w.humidity,
               w.pressure_hpa, w.wind_speed_mps, w.weather_condition,
               w.timestamp
        FROM weather_records w
        JOIN cities c ON w.city_id = c.city_id
        WHERE w.record_id IN (
            SELECT MAX(record_id) FROM weather_records GROUP BY city_id
        )
        ORDER BY w.temperature_c DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_city_stats():
    """Get aggregate stats per city across all records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.city_name,
               COUNT(w.record_id)          AS total_records,
               ROUND(AVG(w.temperature_c), 2) AS avg_temp,
               ROUND(MAX(w.temperature_c), 2) AS max_temp,
               ROUND(MIN(w.temperature_c), 2) AS min_temp,
               ROUND(AVG(w.humidity), 1)    AS avg_humidity,
               ROUND(AVG(w.wind_speed_mps), 2) AS avg_wind
        FROM weather_records w
        JOIN cities c ON w.city_id = c.city_id
        GROUP BY c.city_name
        ORDER BY avg_temp DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_recent_alerts():
    """Get all alerts from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.city_name, a.alert_type, a.alert_value,
               a.threshold, a.created_at
        FROM alerts a
        JOIN cities c ON a.city_id = c.city_id
        ORDER BY a.created_at DESC
        LIMIT 20
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_temperature_ranking():
    """Rank cities by their latest temperature."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.city_name, w.temperature_c, w.weather_condition
        FROM weather_records w
        JOIN cities c ON w.city_id = c.city_id
        WHERE w.record_id IN (
            SELECT MAX(record_id) FROM weather_records GROUP BY city_id
        )
        ORDER BY w.temperature_c DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows


def print_report():
    """Print a full weather report to the console."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print("\n" + "=" * 60)
    print("        WEATHER DATA PIPELINE — FULL REPORT")
    print(f"        Generated: {now}")
    print("=" * 60)

    # --- Current Snapshot ---
    print("\n🌤️  CURRENT WEATHER SNAPSHOT (latest per city)")
    print("-" * 60)
    snapshot = get_latest_snapshot()
    for row in snapshot:
        city, country, temp, feels, humidity, pressure, wind, condition, ts = row
        print(f"  📍 {city:<14} {temp:>6}°C  (feels {feels}°C) | "
              f"{humidity}% humidity | {condition}")

    # --- Temperature Ranking ---
    print("\n🏆  TEMPERATURE RANKING (hottest → coldest)")
    print("-" * 60)
    ranking = get_temperature_ranking()
    for i, row in enumerate(ranking, 1):
        city, temp, condition = row
        bar = "█" * int(temp / 2) if temp > 0 else ""
        print(f"  {i:>2}. {city:<14} {temp:>6}°C  {bar}")

    # --- City Statistics ---
    print("\n📊  CITY STATISTICS (all-time)")
    print("-" * 60)
    print(f"  {'City':<14} {'Records':>7} {'Avg°C':>7} {'Max°C':>7} "
          f"{'Min°C':>7} {'Humidity':>9} {'Wind':>6}")
    print("  " + "-" * 56)
    stats = get_city_stats()
    for row in stats:
        city, records, avg_t, max_t, min_t, avg_h, avg_w = row
        print(f"  {city:<14} {records:>7} {avg_t:>7} {max_t:>7} "
              f"{min_t:>7} {avg_h:>8}% {avg_w:>5} m/s")

    # --- Alerts ---
    print("\n⚠️   RECENT ALERTS")
    print("-" * 60)
    alerts = get_recent_alerts()
    if alerts:
        for row in alerts:
            city, alert_type, value, threshold, created_at = row
            icons = {
                'HIGH_TEMP':     '🌡️ ',
                'LOW_TEMP':      '🥶',
                'HIGH_HUMIDITY': '💧',
                'HIGH_WIND':     '💨'
            }
            icon = icons.get(alert_type, '⚠️ ')
            print(f"  {icon} [{city}] {alert_type}: {value} "
                  f"(threshold: {threshold}) @ {created_at}")
    else:
        print("  ✅ No alerts on record.")

    print("\n" + "=" * 60 + "\n")


def save_report_to_file():
    """Save the report as a timestamped .txt file in the reports folder."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(REPORT_DIR, f"weather_report_{timestamp}.txt")

    # Redirect stdout to file
    import io
    from contextlib import redirect_stdout

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_report()

    report_text = buffer.getvalue()

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"📁 Report saved to: {filepath}")
    return filepath


if __name__ == "__main__":
    print_report()
    save_report_to_file()