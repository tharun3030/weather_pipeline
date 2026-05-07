# Weather Data Pipeline System

An end-to-end ETL pipeline that collects real-time weather data from
OpenWeatherMap, stores it in a SQLite database, and provides automated
reporting, alerting, and monitoring.

---

## Project Structure
weather_pipeline/
├── main.py               # Entry point — interactive menu
├── requirements.txt      # Python dependencies
├── config/
│   └── config.py         # API key, cities, thresholds
├── src/
│   ├── database.py       # DB setup, insert & query functions
│   ├── api_client.py     # OpenWeatherMap API integration
│   ├── etl_pipeline.py   # Extract → Transform → Validate → Load
│   ├── validators.py     # Data quality checks
│   ├── scheduler.py      # Automated scheduling
│   ├── reporter.py       # Report generation
│   └── monitor.py        # Pipeline health monitoring
├── database/
│   └── weather_data.db   # SQLite database (auto-created)
├── logs/
│   └── pipeline.log      # System logs (auto-created)
├── reports/              # Saved report files (auto-created)
├── tests/                # Unit tests
└── docs/                 # Documentation

---

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- OpenWeatherMap free API key — sign up at openweathermap.org

### 2. Clone and install

```bash
git clone <your-repo-url>
cd weather_pipeline
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Configure API key

Open `config/config.py` and replace:
```python
API_KEY = "your_api_key_here"
```
with your actual OpenWeatherMap API key.

### 4. Run the application

```bash
python main.py
```

---

## Database Schema

### Table 1: cities
| Column     | Type    | Description              |
|------------|---------|--------------------------|
| city_id    | INTEGER | Primary key              |
| city_name  | TEXT    | Unique city name         |
| country    | TEXT    | Country code             |
| latitude   | REAL    | Geographic latitude      |
| longitude  | REAL    | Geographic longitude     |
| created_at | TIMESTAMP | Record creation time  |

### Table 2: weather_records
| Column           | Type      | Description                   |
|------------------|-----------|-------------------------------|
| record_id        | INTEGER   | Primary key                   |
| city_id          | INTEGER   | Foreign key → cities          |
| timestamp        | TIMESTAMP | Time of data collection       |
| temperature_c    | REAL      | Temperature in Celsius        |
| feels_like_c     | REAL      | Feels-like temperature        |
| temp_min_c       | REAL      | Minimum temperature           |
| temp_max_c       | REAL      | Maximum temperature           |
| humidity         | INTEGER   | Humidity percentage           |
| pressure_hpa     | REAL      | Atmospheric pressure (hPa)    |
| wind_speed_mps   | REAL      | Wind speed (m/s)              |
| wind_direction   | INTEGER   | Wind direction (degrees)      |
| visibility_m     | INTEGER   | Visibility (metres)           |
| weather_condition| TEXT      | Description (e.g. clear sky)  |
| weather_icon     | TEXT      | OWM icon code                 |

### Table 3: alerts
| Column      | Type      | Description                    |
|-------------|-----------|--------------------------------|
| alert_id    | INTEGER   | Primary key                    |
| city_id     | INTEGER   | Foreign key → cities           |
| record_id   | INTEGER   | Foreign key → weather_records  |
| alert_type  | TEXT      | HIGH_TEMP / LOW_TEMP / etc.    |
| alert_value | REAL      | The value that triggered alert |
| threshold   | REAL      | The configured threshold       |
| created_at  | TIMESTAMP | When alert was logged          |

---

## ETL Pipeline
OpenWeatherMap API
│
▼
EXTRACT (api_client.py)
Fetch weather for all 10 cities
│
▼
TRANSFORM (etl_pipeline.py)
Clean, round, enrich with heat category
│
▼
VALIDATE (validators.py)
Check ranges, required fields, types
│
▼
LOAD (database.py)
Insert cities, records, trigger alerts
│
▼
REPORT / MONITOR
reporter.py + monitor.py

---

## Alert Thresholds

| Alert Type    | Condition                  |
|---------------|----------------------------|
| HIGH_TEMP     | Temperature > 35°C         |
| LOW_TEMP      | Temperature < 0°C          |
| HIGH_HUMIDITY | Humidity > 85%             |
| HIGH_WIND     | Wind speed > 15 m/s        |

---

## Usage

| Menu Option | Action                              |
|-------------|-------------------------------------|
| 1           | Run the full ETL pipeline once      |
| 2           | Print weather report to console     |
| 3           | Save report to reports/ folder      |
| 4           | Run database quality checks         |
| 5           | Check pipeline health status        |
| 6           | Start automated scheduler (60 min)  |

---

## Dependencies
requests
pandas
schedule
python-dotenv
tabulate

Install with: `pip install -r requirements.txt`

---

## Data Source

OpenWeatherMap API (free tier)
- Endpoint: `api.openweathermap.org/data/2.5/weather`
- Rate limit: 60 calls/minute
- Documentation: openweathermap.org/api