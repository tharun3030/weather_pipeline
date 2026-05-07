import sys
import os
import unittest
import sqlite3
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.validators import validate_record, validate_batch
from src.etl_pipeline import transform


class TestValidators(unittest.TestCase):

    def test_valid_record_passes(self):
        record = {
            'city_name': 'London',
            'country': 'GB',
            'temperature_c': 15.0,
            'feels_like_c': 13.0,
            'temp_min_c': 12.0,
            'temp_max_c': 17.0,
            'humidity': 70,
            'pressure_hpa': 1013.0,
            'wind_speed_mps': 5.0,
            'wind_direction': 180,
            'visibility_m': 10000,
            'weather_condition': 'clear sky',
            'weather_icon': '01d'
        }
        is_valid, errors = validate_record(record)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_missing_temperature_fails(self):
        record = {
            'city_name': 'London',
            'country': 'GB',
            'temperature_c': None,
            'humidity': 70,
            'pressure_hpa': 1013.0,
            'wind_speed_mps': 5.0,
            'weather_condition': 'clear sky',
        }
        is_valid, errors = validate_record(record)
        self.assertFalse(is_valid)
        self.assertTrue(any('temperature_c' in e for e in errors))

    def test_temperature_out_of_range_fails(self):
        record = {
            'city_name': 'Mars',
            'country': 'XX',
            'temperature_c': -200.0,  # Below -90 limit
            'humidity': 50,
            'pressure_hpa': 1013.0,
            'wind_speed_mps': 5.0,
            'weather_condition': 'unknown',
        }
        is_valid, errors = validate_record(record)
        self.assertFalse(is_valid)
        self.assertTrue(any('temperature_c' in e for e in errors))

    def test_humidity_out_of_range_fails(self):
        record = {
            'city_name': 'London',
            'country': 'GB',
            'temperature_c': 15.0,
            'humidity': 150,  # Over 100 limit
            'pressure_hpa': 1013.0,
            'wind_speed_mps': 5.0,
            'weather_condition': 'clear sky',
        }
        is_valid, errors = validate_record(record)
        self.assertFalse(is_valid)
        self.assertTrue(any('humidity' in e for e in errors))

    def test_missing_city_name_fails(self):
        record = {
            'city_name': '',
            'country': 'GB',
            'temperature_c': 15.0,
            'humidity': 70,
            'pressure_hpa': 1013.0,
            'wind_speed_mps': 5.0,
            'weather_condition': 'clear sky',
        }
        is_valid, errors = validate_record(record)
        self.assertFalse(is_valid)

    def test_validate_batch_separates_valid_invalid(self):
        records = [
            {
                'city_name': 'London', 'country': 'GB',
                'temperature_c': 15.0, 'humidity': 70,
                'pressure_hpa': 1013.0, 'wind_speed_mps': 5.0,
                'weather_condition': 'clear sky',
            },
            {
                'city_name': 'BadCity', 'country': 'XX',
                'temperature_c': -999.0,  # Invalid
                'humidity': 70,
                'pressure_hpa': 1013.0, 'wind_speed_mps': 5.0,
                'weather_condition': 'weird',
            }
        ]
        valid, invalid = validate_batch(records)
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 1)


class TestTransform(unittest.TestCase):

    def get_sample_raw(self, city='London', temp=15.123, humidity=70):
        return {
            'city_name': city,
            'country': 'GB',
            'latitude': 51.5,
            'longitude': -0.1,
            'temperature_c': temp,
            'feels_like_c': temp - 2,
            'temp_min_c': temp - 3,
            'temp_max_c': temp + 3,
            'humidity': humidity,
            'pressure_hpa': 1013.0,
            'wind_speed_mps': 4.567,
            'wind_direction': 180,
            'visibility_m': 10000,
            'weather_condition': 'clear sky',
            'weather_icon': '01d',
            'fetched_at': '2026-01-01 12:00:00'
        }

    def test_transform_rounds_temperature(self):
        result = transform([self.get_sample_raw(temp=15.12345)])
        self.assertEqual(result[0]['temperature_c'], 15.12)

    def test_transform_rounds_wind_speed(self):
        result = transform([self.get_sample_raw()])
        self.assertEqual(result[0]['wind_speed_mps'], 4.57)

    def test_heat_category_extreme(self):
        result = transform([self.get_sample_raw(temp=38.0)])
        self.assertEqual(result[0]['heat_category'], 'Extreme')

    def test_heat_category_hot(self):
        result = transform([self.get_sample_raw(temp=30.0)])
        self.assertEqual(result[0]['heat_category'], 'Hot')

    def test_heat_category_warm(self):
        result = transform([self.get_sample_raw(temp=22.0)])
        self.assertEqual(result[0]['heat_category'], 'Warm')

    def test_heat_category_mild(self):
        result = transform([self.get_sample_raw(temp=15.0)])
        self.assertEqual(result[0]['heat_category'], 'Mild')

    def test_heat_category_cold(self):
        result = transform([self.get_sample_raw(temp=-5.0)])
        self.assertEqual(result[0]['heat_category'], 'Cold')

    def test_transform_skips_missing_temperature(self):
        record = self.get_sample_raw()
        record['temperature_c'] = None
        result = transform([record])
        self.assertEqual(len(result), 0)

    def test_transform_skips_missing_humidity(self):
        record = self.get_sample_raw()
        record['humidity'] = None
        result = transform([record])
        self.assertEqual(len(result), 0)

    def test_transform_handles_multiple_cities(self):
        records = [
            self.get_sample_raw('London', 15.0),
            self.get_sample_raw('Dubai', 41.0),
            self.get_sample_raw('Toronto', 3.0),
        ]
        result = transform(records)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['heat_category'], 'Mild')
        self.assertEqual(result[1]['heat_category'], 'Extreme')
        self.assertEqual(result[2]['heat_category'], 'Cold')


if __name__ == '__main__':
    unittest.main(verbosity=2)