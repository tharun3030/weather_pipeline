import os

# --- API Settings ---
API_KEY = "your_api_key_here"  # Replace with your OpenWeatherMap API key
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# --- Cities to Track ---
CITIES = [
    "London",
    "New York",
    "Tokyo",
    "Mumbai",
    "Sydney",
    "Paris",
    "Dubai",
    "Singapore",
    "Cairo",
    "Toronto"
]

# --- Database Settings ---
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "weather_data.db")

# --- Scheduler Settings ---
FETCH_INTERVAL_MINUTES = 60  # How often to collect data

# --- Alert Thresholds ---
TEMP_HIGH_THRESHOLD = 35.0   # Celsius
TEMP_LOW_THRESHOLD = 0.0     # Celsius
HUMIDITY_HIGH_THRESHOLD = 85  # Percent
WIND_HIGH_THRESHOLD = 15.0   # m/s

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
REPORT_DIR = os.path.join(BASE_DIR, "reports")