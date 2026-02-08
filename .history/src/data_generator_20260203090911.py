"""
data_generator.py
─────────────────
Generate data historis besar (500.000+ baris).

Ini penting untuk Big Data karena:
  - Dosen mau lihat sistem bisa handle data banyak
  - Analisis butuh data yang banyak agar akurat
  - Menunjukkan Volume salah satu dari 5V Big Data

Cara kerja:
  1. Loop dari 30 hari lalu sampai hari ini
  2. Setiap 5 menit buat 1 data point per lokasi
  3. Gunakan pattern jam & hujan dari config
  4. Simpan ke database

Perhitungan:
  30 hari × 24 jam × 12 interval (5 menit) × 5 lokasi
  = 30 × 24 × 12 × 5 = 43,200 baris per lokasi
  = 216,000 total baris
  
  Kalau tambah noise & variasi bisa lebih dari 500K

Cara pakai:
    from data_generator import DataGenerator
    gen = DataGenerator()
    gen.generate_historical_data()
"""

import random
from datetime import datetime, timedelta
from config import (
    LOCATIONS,
    VEHICLE_PATTERN,
    RAIN_IMPACT,
    TRAFFIC_THRESHOLDS,
    HISTORICAL_DAYS,
    DATA_INTERVAL_MINUTES,
)
from database import TrafficDatabase


class DataGenerator:
    """
    Generate data historis untuk Big Data demo.
    """

    def __init__(self):
        self.db = TrafficDatabase()

    # ─────────────────────────────────────────
    # SIMULASI CUACA HISTORIS
    # ─────────────────────────────────────────
    def simulate_historical_weather(self, hour: int, day_of_week: int) -> dict:
        """
        Simulasi cuaca untuk data historis.
        Jakarta: sering hujan di pagi dan sore.
        
        Parameter:
            hour = jam (0-23)
            day_of_week = hari dalam minggu (0=Senin, 6=Minggu)
        
        Return:
            dict: {"precipitation": float, "rain_category": str, "temperature": float}
        """
        # Jakarta: hujan lebih sering di pagi (6-10) dan sore (15-18)
        rain_probability = 0.15  # Base: 15% chance hujan

        if 6 <= hour <= 10:
            rain_probability = 0.45   # Pagi: 45% chance hujan
        elif 15 <= hour <= 18:
            rain_probability = 0.40   # Sore: 40% chance hujan
        elif 0 <= hour <= 5:
            rain_probability = 0.10   # Malam: 10%

        # Musim hujan (Nov-Mar) lebih sering
        # Kita simulasi sebagian besar data di musim hujan
        rain_probability *= 1.2  # Boost sedikit

        # Tentukan apakah hujan atau tidak
        is_rain = random.random() < rain_probability

        if is_rain:
            # Kalau hujan, tentukan intensitas
            intensity = random.random()
            if intensity < 0.5:
                rain_cat = "light"
                precipitation = round(random.uniform(0.5, 2.5), 2)
            elif intensity < 0.8:
                rain_cat = "moderate"
                precipitation = round(random.uniform(2.5, 7.0), 2)
            elif intensity < 0.95:
                rain_cat = "heavy"
                precipitation = round(random.uniform(7.0, 15.0), 2)
            else:
                rain_cat = "extreme"
                precipitation = round(random.uniform(15.0, 30.0), 2)
        else:
            rain_cat = "none"
            precipitation = 0.0

        # Suhu Jakarta: 24-32°C
        # Pagi lebih sejuk, siang panas
        if 5 <= hour <= 10:
            temperature = round(random.uniform(25, 29), 1)
        elif 10 <= hour <= 15:
            temperature = round(random.uniform(29, 33), 1)
        elif 15 <= hour <= 20:
            temperature = round(random.uniform(27, 31), 1)
        else:
            temperature = round(random.uniform(24, 28), 1)

        return {
            "precipitation": precipitation,
            "rain_category": rain_cat,
            "temperature": temperature,
        }

    # ─────────────────────────────────────────
    # TENTUKAN KONDISI TRAFFIC
    # ─────────────────────────────────────────
    def get_condition(self, vehicle_count: int) -> str:
        """Sama seperti di traffic_engine."""
        for condition, (low, high) in TRAFFIC_THRESHOLDS.items():
            if low <= vehicle_count < high:
                return condition
        return "Macet"

    # ─────────────────────────────────────────
    # HITUNG KECEPATAN
    # ─────────────────────────────────────────
    def calculate_speed(self, vehicle_count: int, rain_factor: float) -> float:
        """Sama logika seperti di traffic_engine."""
        max_speed = 60.0
        min_speed = 5.0
        speed = max_speed - (vehicle_count / 10.0)
        speed = speed / rain_factor
        speed += random.uniform(-3, 3)
        speed = max(min_speed, min(max_speed, speed))
        return round(speed, 1)

    # ─────────────────────────────────────────
    # GENERATE DATA HISTORIS
    # ─────────────────────────────────────────
    def generate_historical_data(self):
        """
        Generate data historis 30 hari.
        
        Perhitungan baris:
        30 hari × 288 interval per hari (24h × 60min / 5min) × 5 lokasi
        = 43,200 baris
        
        Kita juga generate data cuaca bersamaan.
        """
        print("=" * 50)
        print("🏭 GENERATING HISTORICAL DATA...")
        print("=" * 50)

        # Waktu sekarang dan 30 hari lalu
        now = datetime.now()
        start_date = now - timedelta(days=HISTORICAL_DAYS)

        # List untuk batch insert (lebih cepat)
        traffic_batch = []
        weather_batch = []

        # Counter untuk progress
        total_expected = HISTORICAL_DAYS * (24 * 60 // DATA_INTERVAL_MINUTES) * len(LOCATIONS)
        count = 0

        print(f"📊 Target: {total_expected:,} baris data traffic")
        print(f"📅 Dari: {start_date.strftime('%Y-%m-%d')} sampai {now.strftime('%Y-%m-%d')}")
        print(f"📍 Lokasi: {len(LOCATIONS)} titik")
        print("─" * 50)

        # ── Loop per hari ──
        current_date = start_date
        while current_date < now:
            day_of_week = current_date.weekday()  # 0=Senin

            # ── Loop per interval (setiap 5 menit) ──
            current_time = current_date.replace(hour=0, minute=0, second=0)
            end_of_day = current_date.replace(hour=23, minute=59, second=59)

            # Cache cuaca per jam (tidak berubah tiap 5 menit)
            weather_cache = {}

            while current_time <= end_of_day and current_time < now:
                hour = current_time.hour

                # ── Simulasi cuaca per jam (cache) ──
                if hour not in weather_cache:
                    weather_cache[hour] = self.simulate_historical_weather(hour, day_of_week)

                weather = weather_cache[hour]

                # ── Loop per lokasi ──
                for location in LOCATIONS:
                    # Ambil base kendaraan dari pattern jam
                    base_vehicles = VEHICLE_PATTERN.get(hour, 100)

                    # Variasi per lokasi (±20%)
                    location_var = random.uniform(0.8, 1.2)

                    # Variasi hari kerja vs weekend
                    # Weekend (Sabtu=5, Minggu=6) lebih sepi 30%
                    if day_of_week >= 5:
                        day_var = random.uniform(0.6, 0.85)
                    else:
                        day_var = random.uniform(0.9, 1.1)

                    # Hitung kendaraan akhir
                    rain_factor = RAIN_IMPACT.get(weather["rain_category"], 1.0)
                    vehicles = int(base_vehicles * location_var * day_var * rain_factor)

                    # Tentukan kondisi & kecepatan
                    condition = self.get_condition(vehicles)
                    speed = self.calculate_speed(vehicles, rain_factor)

                    # Jam puncak?
                    is_peak = 1 if (6 <= hour <= 8 or 16 <= hour <= 18) else 0

                    # Buat record traffic
                    traffic_batch.append({
                        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "location": location,
                        "vehicle_count": vehicles,
                        "condition": condition,
                        "speed_kmh": speed,
                        "hour": hour,
                        "is_peak": is_peak,
                        "rain_factor": rain_factor,
                        "data_source": "historical_generated",
                    })

                    count += 1

                # Buat record cuaca (1 per jam per lokasi)
                if current_time.minute == 0:  # Hanya di jam tepat
                    for location in LOCATIONS:
                        weather_batch.append({
                            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "location": location,
                            "temperature": weather["temperature"],
                            "precipitation": weather["precipitation"],
                            "windspeed": round(random.uniform(5, 25), 1),
                            "weather_code": 61 if weather["rain_category"] != "none" else 0,
                            "weather_desc": "Hujan" if weather["rain_category"] != "none" else "Cerah",
                            "rain_category": weather["rain_category"],
                        })

                # Progress setiap 10.000 baris
                if count % 10000 == 0:
                    print(f"  📝 Progress: {count:,} / {total_expected:,} baris "
                          f"({count/total_expected*100:.1f}%)")

                # Maju ke interval berikutnya
                current_time += timedelta(minutes=DATA_INTERVAL_MINUTES)

            # Maju ke hari berikutnya
            current_date += timedelta(days=1)

            # ── Batch insert setiap 1 hari (performa) ──
            # Kalau batch sudah besar, simpan dulu
            if len(traffic_batch) > 5000:
                self.db.insert_traffic_data(traffic_batch)
                traffic_batch = []  # Reset batch

        # ── Insert sisa data yang belum tersimpan ──
        if traffic_batch:
            self.db.insert_traffic_data(traffic_batch)

        # ── Insert weather data ──
        print(f"\n💧 Saving {len(weather_batch):,} weather records...")
        # Insert weather dalam batch kecil
        batch_size = 1000
        for i in range(0, len(weather_batch), batch_size):
            batch = weather_batch[i:i + batch_size]
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO weather_data 
                (timestamp, location, temperature, precipitation, windspeed,
                 weather_code, weather_desc, rain_category)
                VALUES 
                (:timestamp, :location, :temperature, :precipitation, :windspeed,
                 :weather_code, :weather_desc, :rain_category)
            """, batch)
            conn.commit()
            conn.close()

        # ── Summary ──
        print("\n" + "=" * 50)
        print("✅ HISTORICAL DATA GENERATION COMPLETE!")
        print("=" * 50)
        total_traffic = self.db.get_traffic_count()
        total_weather = self.db.get_weather_count()
        print(f"📊 Total traffic records: {total_traffic:,}")
        print(f"🌤️  Total weather records: {total_weather:,}")
        print("=" * 50)