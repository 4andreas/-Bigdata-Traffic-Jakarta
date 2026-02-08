"""
traffic_engine.py
─────────────────
Engine simulasi traffic real-time.

Cara kerja:
1. Ambil jam sekarang
2. Lihat pattern kendaraan berdasarkan jam (dari config)
3. Lihat kondisi cuaca sekarang (dari weather_api)
4. Hitung jumlah kendaraan (pattern × rain_factor)
5. Tentukan kondisi traffic (Lancar / Padat / Macet)
6. Hitung kecepatan rata-rata
7. Simpan ke database

Cara pakai:
    from traffic_engine import TrafficEngine
    engine = TrafficEngine()
    engine.run_simulation_cycle()
"""

import random
from datetime import datetime
from config import (
    LOCATIONS,
    VEHICLE_PATTERN,
    RAIN_IMPACT,
    TRAFFIC_THRESHOLDS,
    PEAK_MORNING,
    PEAK_EVENING,
)
from database import TrafficDatabase
from weather_api import WeatherAPI


class TrafficEngine:
    """
    Engine untuk simulasi traffic.
    Menggabungkan data cuaca + pattern jam → hasil traffic.
    """

    def __init__(self):
        self.db = TrafficDatabase()
        self.weather_api = WeatherAPI()
        # Simpan cuaca terakhir (cache)
        self.last_weather = {}

    # ─────────────────────────────────────────
    # CEK JAM PUNCAK
    # ─────────────────────────────────────────
    def is_peak_hour(self, hour: int) -> bool:
        """
        Cek apakah jam ini termasuk jam puncak.
        
        Parameter:
            hour = jam sekarang (0-23)
        
        Return:
            True kalau jam puncak, False kalau bukan
        """
        is_morning_peak = PEAK_MORNING["start"] <= hour < PEAK_MORNING["end"]
        is_evening_peak = PEAK_EVENING["start"] <= hour < PEAK_EVENING["end"]
        return is_morning_peak or is_evening_peak

    # ─────────────────────────────────────────
    # TENTUKAN KONDISI TRAFFIC
    # ─────────────────────────────────────────
    def get_traffic_condition(self, vehicle_count: int) -> str:
        """
        Tentukan kondisi traffic berdasarkan jumlah kendaraan.
        
        Parameter:
            vehicle_count = jumlah kendaraan
        
        Return:
            str: "Lancar", "Sedang", "Padat", "Sangat Padat", atau "Macet"
        """
        for condition, (low, high) in TRAFFIC_THRESHOLDS.items():
            if low <= vehicle_count < high:
                return condition
        return "Macet"  # Default kalau lebih dari semua threshold

    # ─────────────────────────────────────────
    # HITUNG KECEPATAN
    # ─────────────────────────────────────────
    def calculate_speed(self, vehicle_count: int, rain_factor: float) -> float:
        """
        Hitung kecepatan rata-rata berdasarkan kepadatan & hujan.
        
        Logic:
        - Semakin banyak kendaraan → semakin lambat
        - Semakin hujan → semakin lambat
        - Kecepatan max di Jakarta = 60 km/h
        - Kecepatan min = 5 km/h (macet total)
        
        Parameter:
            vehicle_count = jumlah kendaraan
            rain_factor = pengaruh hujan (1.0 = normal)
        
        Return:
            float: kecepatan dalam km/h
        """
        max_speed = 60.0   # Kecepatan max
        min_speed = 5.0    # Kecepatan min (macet)

        # Semakin banyak kendaraan, kecepatan turun
        # Formula: speed = max_speed - (vehicle_count / 10)
        speed = max_speed - (vehicle_count / 10.0)

        # Pengaruh hujan (kurangi kecepatan)
        speed = speed / rain_factor

        # Tambah sedikit randomness (realistis)
        speed += random.uniform(-3, 3)

        # Clamp: pastikan speed di antara min dan max
        speed = max(min_speed, min(max_speed, speed))

        return round(speed, 1)

    # ─────────────────────────────────────────
    # SIMULASI 1 LOKASI
    # ─────────────────────────────────────────
    def simulate_location(self, location: str, weather_data: dict = None) -> dict:
        """
        Simulasi traffic untuk 1 lokasi.
        
        Parameter:
            location = nama lokasi
            weather_data = data cuaca (optional, kalau None akan fetch baru)
        
        Return:
            dict berisi hasil simulasi
        """
        now = datetime.now()
        hour = now.hour

        # ── 1. Ambil base vehicle count dari pattern jam ──
        base_vehicles = VEHICLE_PATTERN.get(hour, 100)

        # ── 2. Tambah randomness per lokasi ──
        # Setiap lokasi sedikit beda (±20%)
        location_variance = random.uniform(0.8, 1.2)
        vehicles = int(base_vehicles * location_variance)

        # ── 3. Hitung pengaruh hujan ──
        rain_factor = 1.0  # Default: tidak hujan

        if weather_data:
            rain_cat = weather_data.get("rain_category", "none")
            rain_factor = RAIN_IMPACT.get(rain_cat, 1.0)
            # Kalau hujan, kendaraan yang macet bertambah
            vehicles = int(vehicles * rain_factor)

        # ── 4. Tentukan kondisi ──
        condition = self.get_traffic_condition(vehicles)

        # ── 5. Hitung kecepatan ──
        speed = self.calculate_speed(vehicles, rain_factor)

        # ── 6. Cek jam puncak ──
        is_peak = 1 if self.is_peak_hour(hour) else 0

        # ── 7. Buat result ──
        result = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "location": location,
            "vehicle_count": vehicles,
            "condition": condition,
            "speed_kmh": speed,
            "hour": hour,
            "is_peak": is_peak,
            "rain_factor": rain_factor,
            "data_source": "real_time_simulated",
        }

        return result

    # ─────────────────────────────────────────
    # SIMULASI SEMUA LOKASI (1 SIKLUS)
    # ─────────────────────────────────────────
    def run_simulation_cycle(self) -> list:
        """
        Jalankan 1 siklus simulasi untuk SEMUA lokasi.
        
        Steps:
        1. Fetch cuaca terbaru dari API
        2. Simulasi traffic per lokasi
        3. Simpan semua ke database
        
        Return:
            list of dict (hasil simulasi semua lokasi)
        """
        print("\n🔄 Running simulation cycle...")
        print("─" * 40)

        # ── Step 1: Fetch cuaca ──
        weather_list = self.weather_api.fetch_and_save()

        # Buat dictionary cuaca per lokasi (mudah dicari)
        weather_map = {}
        for w in weather_list:
            weather_map[w["location"]] = w

        # ── Step 2: Simulasi traffic per lokasi ──
        traffic_records = []

        for location in LOCATIONS:
            # Ambil cuaca untuk lokasi ini
            weather = weather_map.get(location)

            # Simulasi
            traffic = self.simulate_location(location, weather)
            traffic_records.append(traffic)

            # Print status
            emoji = "🟢" if traffic["condition"] == "Lancar" else \
                    "🟡" if traffic["condition"] == "Sedang" else \
                    "🟠" if traffic["condition"] == "Padat" else \
                    "🔴"
            print(f"  {emoji} {location}: "
                  f"{traffic['vehicle_count']} kendaraan, "
                  f"{traffic['condition']}, "
                  f"{traffic['speed_kmh']} km/h")

        # ── Step 3: Simpan ke database ──
        self.db.insert_traffic_data(traffic_records)

        print("─" * 40)
        print(f"✅ Simulation cycle complete! {len(traffic_records)} records saved\n")

        return traffic_records