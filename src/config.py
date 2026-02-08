import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORICAL_DIR = os.path.join(DATA_DIR, "historical")
WEATHER_DIR = os.path.join(DATA_DIR, "weather")
DATABASE_PATH = os.path.join(DATA_DIR, "traffic_bigdata.db")

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

LOCATIONS = {
    "Jakarta Pusat":  {"lat": -6.2088,  "lon": 106.8456},
    "Jakarta Selatan": {"lat": -6.2614, "lon": 106.8456},
    "Jakarta Utara":  {"lat": -6.1361,  "lon": 106.8513},
    "Jakarta Timur":  {"lat": -6.2297,  "lon": 106.9012},
    "Jakarta Barat":  {"lat": -6.1847,  "lon": 106.7513},
}

WEATHER_PARAMS = {
    "latitude": None,
    "longitude": None,
    "current_weather": "true",
    "hourly": "temperature_2m,precipitation,windspeed_10m,weathercode",
    "timezone": "Asia/Jakarta",
    "forecast_days": 1,
}

PEAK_MORNING = {"start": 6, "end": 9}
PEAK_EVENING = {"start": 16, "end": 19}

VEHICLE_PATTERN = {
    0: 50, 1: 40, 2: 35, 3: 30, 4: 40, 5: 80,
    6: 200, 7: 350, 8: 400, 9: 250, 10: 180, 11: 200,
    12: 220, 13: 200, 14: 180, 15: 200, 16: 300,
    17: 420, 18: 380, 19: 250, 20: 180, 21: 150,
    22: 120, 23: 80,
}

RAIN_IMPACT = {
    "none": 1.0,
    "light": 1.3,
    "moderate": 1.6,
    "heavy": 1.8,
    "extreme": 2.0,
}

TRAFFIC_THRESHOLDS = {
    "Lancar":      (0, 100),
    "Sedang":      (100, 200),
    "Padat":       (200, 350),
    "Sangat Padat": (350, 500),
    "Macet":       (500, 9999),
}

HISTORICAL_DAYS = 30
DATA_INTERVAL_MINUTES = 5