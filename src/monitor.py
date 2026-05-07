import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database import get_connection
from config.config import LOG_DIR
from datetime import datetime, timedelta


def check_pipeline_health():
    """Check if the pipeline has run recently and data looks healthy."""
    conn = get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 50)
    print("  PIPELINE HEALTH MONITOR")
    print(f"  Checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    issues = []

    # Check 1: Total records
    cursor.execute("SELECT COUNT(*) FROM weather_records")
    total = cursor.fetchone()[0]
    status = "✅" if total > 0 else "❌"
    print(f"\n  {status} Total records in DB   : {total}")
    if total == 0:
        issues.append("No records in database")

    # Check 2: Last run time
    cursor.execute("SELECT MAX(timestamp) FROM weather_records")
    last_run = cursor.fetchone()[0]
    if last_run:
        last_run_dt = datetime.strptime(last_run[:19], '%Y-%m-%d %H:%M:%S')
        age_minutes = (datetime.now() - last_run_dt).total_seconds() / 60
        status = "✅" if age_minutes < 120 else "⚠️ "
        print(f"  {status} Last data collected    : {last_run} ({int(age_minutes)} min ago)")
        if age_minutes > 120:
            issues.append(f"No new data in {int(age_minutes)} minutes")
    else:
        print("  ❌ Last data collected    : Never")
        issues.append("Pipeline has never run")

    # Check 3: Cities tracked
    cursor.execute("SELECT COUNT(*) FROM cities")
    city_count = cursor.fetchone()[0]
    status = "✅" if city_count >= 5 else "⚠️ "
    print(f"  {status} Cities tracked         : {city_count}")
    if city_count < 5:
        issues.append(f"Only {city_count} cities tracked (expected 10)")

    # Check 4: Alerts logged
    cursor.execute("SELECT COUNT(*) FROM alerts")
    alert_count = cursor.fetchone()[0]
    print(f"  ✅ Total alerts logged     : {alert_count}")

    # Check 5: Data freshness per city
    print("\n  📍 Per-city freshness:")
    cursor.execute('''
        SELECT c.city_name, MAX(w.timestamp) as last_seen
        FROM cities c
        LEFT JOIN weather_records w ON c.city_id = w.city_id
        GROUP BY c.city_name
        ORDER BY last_seen DESC
    ''')
    for row in cursor.fetchall():
        city, last_seen = row
        if last_seen:
            last_dt = datetime.strptime(last_seen[:19], '%Y-%m-%d %H:%M:%S')
            age = int((datetime.now() - last_dt).total_seconds() / 60)
            status = "✅" if age < 120 else "⚠️ "
            print(f"     {status} {city:<14} last seen {age} min ago")
        else:
            print(f"     ❌ {city:<14} no data")
            issues.append(f"No data for {city}")

    # Check 6: Log file status
    print("\n  📋 Log file status:")
    log_path = os.path.join(LOG_DIR, "pipeline.log")
    if os.path.exists(log_path):
        size_kb = os.path.getsize(log_path) / 1024
        print(f"     ✅ pipeline.log exists ({size_kb:.1f} KB)")
    else:
        print("     ⚠️  pipeline.log not found")
        issues.append("Log file missing")

    # --- Summary ---
    print("\n" + "-" * 50)
    if not issues:
        print("  ✅ SYSTEM STATUS: HEALTHY — all checks passed")
    else:
        print(f"  ⚠️  SYSTEM STATUS: {len(issues)} issue(s) found:")
        for issue in issues:
            print(f"     • {issue}")
    print("=" * 50 + "\n")

    conn.close()
    return len(issues) == 0


if __name__ == "__main__":
    check_pipeline_health()