import sqlite3
import os
import logging
from config.config import DB_PATH

logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "pipeline.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: cities
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cities (
            city_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            city_name TEXT NOT NULL UNIQUE,
            country   TEXT,
            latitude  REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table 2: weather_records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_records (
            record_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id           INTEGER NOT NULL,
            timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            temperature_c     REAL,
            feels_like_c      REAL,
            temp_min_c        REAL,
            temp_max_c        REAL,
            humidity          INTEGER,
            pressure_hpa      REAL,
            wind_speed_mps    REAL,
            wind_direction    INTEGER,
            visibility_m      INTEGER,
            weather_condition TEXT,
            weather_icon      TEXT,
            FOREIGN KEY (city_id) REFERENCES cities (city_id)
        )
    ''')

    # Table 3: alerts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id     INTEGER NOT NULL,
            record_id   INTEGER NOT NULL,
            alert_type  TEXT NOT NULL,
            alert_value REAL,
            threshold   REAL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (city_id) REFERENCES cities (city_id),
            FOREIGN KEY (record_id) REFERENCES weather_records (record_id)
        )
    ''')

    conn.commit()
    conn.close()
    logging.info("Database setup complete.")
    print("✅ Database and tables created successfully.")


def insert_city(city_name, country, latitude, longitude):
    """Insert a city if it doesn't already exist. Returns city_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO cities (city_name, country, latitude, longitude)
        VALUES (?, ?, ?, ?)
    ''', (city_name, country, latitude, longitude))
    conn.commit()
    cursor.execute('SELECT city_id FROM cities WHERE city_name = ?', (city_name,))
    city_id = cursor.fetchone()[0]
    conn.close()
    return city_id


def insert_weather_record(city_id, data):
    """Insert a weather record. Returns the new record_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO weather_records (
            city_id, temperature_c, feels_like_c, temp_min_c, temp_max_c,
            humidity, pressure_hpa, wind_speed_mps, wind_direction,
            visibility_m, weather_condition, weather_icon
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        city_id,
        data.get('temperature_c'),
        data.get('feels_like_c'),
        data.get('temp_min_c'),
        data.get('temp_max_c'),
        data.get('humidity'),
        data.get('pressure_hpa'),
        data.get('wind_speed_mps'),
        data.get('wind_direction'),
        data.get('visibility_m'),
        data.get('weather_condition'),
        data.get('weather_icon')
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def insert_alert(city_id, record_id, alert_type, alert_value, threshold):
    """Log an alert into the alerts table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO alerts (city_id, record_id, alert_type, alert_value, threshold)
        VALUES (?, ?, ?, ?, ?)
    ''', (city_id, record_id, alert_type, alert_value, threshold))
    conn.commit()
    conn.close()


def get_all_cities():
    """Return all cities from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cities')
    rows = cursor.fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    setup_database()