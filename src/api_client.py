import requests
import logging
import time
from datetime import datetime
from config.config import API_KEY, BASE_URL

def fetch_weather(city_name):
    """
    Fetch current weather data for a city from OpenWeatherMap.
    Returns a clean dictionary or None if the request fails.
    """
    params = {
        'q': city_name,
        'appid': API_KEY,
        'units': 'metric'
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        raw = response.json()
        
        data = {
            'city_name':        raw['name'],
            'country':          raw['sys']['country'],
            'latitude':         raw['coord']['lat'],
            'longitude':        raw['coord']['lon'],
            'temperature_c':    raw['main']['temp'],
            'feels_like_c':     raw['main']['feels_like'],
            'temp_min_c':       raw['main']['temp_min'],
            'temp_max_c':       raw['main']['temp_max'],
            'humidity':         raw['main']['humidity'],
            'pressure_hpa':     raw['main']['pressure'],
            'wind_speed_mps':   raw['wind']['speed'],
            'wind_direction':   raw['wind'].get('deg', None),
            'visibility_m':     raw.get('visibility', None),
            'weather_condition': raw['weather'][0]['description'],
            'weather_icon':     raw['weather'][0]['icon'],
            'fetched_at':       datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        logging.info(f"Fetched weather for {city_name} successfully.")
        return data

    except requests.exceptions.ConnectionError:
        logging.error(f"Connection error for {city_name}. Check your internet.")
        print(f"  ❌ Connection error for {city_name}")
        return None

    except requests.exceptions.Timeout:
        logging.error(f"Request timed out for {city_name}.")
        print(f"  ❌ Timeout for {city_name}")
        return None

    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            logging.error("Invalid API key.")
            print("  ❌ Invalid API key — check config.py")
        elif response.status_code == 404:
            logging.error(f"City not found: {city_name}")
            print(f"  ❌ City not found: {city_name}")
        else:
            logging.error(f"HTTP error for {city_name}: {e}")
            print(f"  ❌ HTTP error for {city_name}: {e}")
        return None

    except Exception as e:
        logging.error(f"Unexpected error for {city_name}: {e}")
        print(f"  ❌ Unexpected error for {city_name}: {e}")
        return None


def fetch_all_cities(city_list):
    """
    Fetch weather for a list of cities.
    Returns a list of successful results and a count of failures.
    """
    results = []
    failures = 0

    print(f"\n🌍 Fetching weather for {len(city_list)} cities...\n")

    for city in city_list:
        print(f"  🔄 Fetching {city}...", end=" ")
        data = fetch_weather(city)
        if data:
            results.append(data)
            print(f"✅ {data['temperature_c']}°C, {data['weather_condition']}")
        else:
            failures += 1
        
        time.sleep(1)  # Avoid rate limiting

    print(f"\n📊 Done — {len(results)} succeeded, {failures} failed.\n")
    return results, failures


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    
    # Quick test with 3 cities
    test_cities = ["London", "Mumbai", "Tokyo"]
    results, failures = fetch_all_cities(test_cities)

    if results:
        print("--- Sample result ---")
        for key, value in results[0].items():
            print(f"  {key}: {value}")