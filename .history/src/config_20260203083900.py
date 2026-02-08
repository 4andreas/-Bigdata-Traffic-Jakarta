"""
config.py
─────────
File ini berisi semua konfigurasi sistem.
Semua URL, path folder, dan setting ada di sini.
Kalau mau ubah sesuatu, ubah di sini aja.
"""

import os

# ─────────────────────────────────────────────
# 1. PATH — Lokasi folder-folder penting
# ─────────────────────────────────────────────
# os.path.dirname(__file__) = folder "src"
# ".." = naik satu level ke "bigdata-traffic"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Folder data
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORICAL_DIR = os.path.join(DATA_DIR, "historical")
WEATHER_DIR = os.path.join(DATA_DIR, "weather")

# Database SQLite (file .db)
DATABASE_PATH = os.path.join(DATA_DIR, "traffic_bigdata.db")

# ─────────────────────────────────────────────
# 2. OPEN-METEO API — Cuaca Gratis
# ─────────────────────────────────────────────
# Open-Meteo: 100% gratis, tidak perlu signup, tidak perlu API key
# Coordinates Jakarta: Latitude -6.2088, Longitude 106.8456
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

# Koordinat Jakarta (bisa tambah kota lain)
LOCATIONS = {
    "Jakarta Pusat":  {"lat": -6.2088,  "lon": 106.8456},
    "Jakarta Selatan": {"lat": -6.2614, "lon": 106.8456},
    "Jakarta Utara":  {"lat": -6.1361,  "lon": 106.8513},
    "Jakarta Timur":  {"lat": -6.2297,  "lon": 106.9012},
    "Jakarta Barat":  {"lat": -6.1847,  "lon": 106.7513},
}

# Parameter cuaca yang diambil dari API
# Penjelasan:
#   temperature_2m       = suhu di ketinggian 2 meter
#   precipitation        = curah hujan (mm)
#   windspeed_10m        = kecepatan angin di 10 meter
#   weathercode          = kode status cuaca (0=cerah, 61=hujan, dst)
WEATHER_PARAMS = {
    "latitude": None,                # Diisi dari LOCATIONS
    "longitude": None,               # Diisi dari LOCATIONS
    "current_weather": "true",       # Cuaca SEKARANG
    "hourly": "temperature_2m,precipitation,windspeed_10m,weathercode",
    "timezone": "Asia/Jakarta",      # Timezone Indonesia
    "forecast_days": 1,              # Hari ini saja
}

# ─────────────────────────────────────────────
# 3. TRAFFIC SIMULATION — Aturan Simulasi
# ─────────────────────────────────────────────
# Jam puncak pagi dan sore
PEAK_MORNING = {"start": 6, "end": 9}     # 06:00 - 09:00
PEAK_EVENING = {"start": 16, "end": 19}   # 16:00 - 19:00

# Jumlah kendaraan per jam berdasarkan waktu
# Ini dipakai untuk simulasi yang realistis
VEHICLE_PATTERN = {
    0: 50,    # 00:00 - tengah malam, sepi
    1: 40,
    2: 35,
    3: 30,
    4: 40,
    5: 80,    # 05:00 - mulai ramai
    6: 200,   # 06:00 - pagi puncak
    7: 350,   # 07:00 - puncak sekali
    8: 400,   # 08:00 - puncak sekali
    9: 250,   # 09:00 - mulai turun
    10: 180,
    11: 200,
    12: 220,  # 12:00 - siang, lumayan ramai
    13: 200,
    14: 180,
    15: 200,
    16: 300,  # 16:00 - sore puncak
    17: 420,  # 17:00 - puncak sekali
    18: 380,  # 18:00 - masih padat
    19: 250,  # 19:00 - mulai turun
    20: 180,
    21: 150,
    22: 120,
    23: 80,   # 23:00 - malam, sepi
}

# ─────────────────────────────────────────────
# 4. KORELASI HUJAN vs TRAFFIC
# ─────────────────────────────────────────────
# Semakin hujan, semakin banyak kemacetan
# Nilai ini = multiplier (pengali) untuk jumlah kendaraan yang macet
# Contoh: hujan lebat = 1.8x → kendaraan macet 1.8 kali lipat
RAIN_IMPACT = {
    "none": 1.0,       # Tidak hujan → normal
    "light": 1.3,      # Hujan ringan → 30% lebih macet
    "moderate": 1.6,   # Hujan sedang → 60% lebih macet
    "heavy": 1.8,      # Hujan lebat → 80% lebih macet
    "extreme": 2.0,    # Hujan ekstrem → 2x macet
}

# ─────────────────────────────────────────────
# 5. KONDISI TRAFFIC
# ─────────────────────────────────────────────
# Berdasarkan jumlah kendaraan, tentukan kondisi
# Threshold = batas angka kendaraan
TRAFFIC_THRESHOLDS = {
    "Lancar":      (0, 100),     # 0-100 kendaraan = lancar
    "Sedang":      (100, 200),   # 100-200 = sedang
    "Padat":       (200, 350),   # 200-350 = padat
    "Sangat Padat": (350, 500),  # 350-500 = sangat padat
    "Macet":       (500, 9999),  # 500+ = macet total
}

# ─────────────────────────────────────────────
# 6. HISTORIS DATA GENERATION
# ─────────────────────────────────────────────
# Berapa hari data historis yang akan di-generate
HISTORICAL_DAYS = 30       # 30 hari ke belakang
# Berapa interval data (dalam menit)
DATA_INTERVAL_MINUTES = 5  # Setiap 5 menit ada 1 data point