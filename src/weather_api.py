"""
weather_api.py
──────────────
Fetch data cuaca REAL dari Open-Meteo API.

Open-Meteo:
  - 100% gratis selamanya
  - Tidak perlu daftar / signup
  - Tidak perlu API key
  - Akurasi tinggi
  - Docs: https://open-meteo.com/en/docs

Cara pakai:
    from weather_api import WeatherAPI
    weather = WeatherAPI()
    
    # Ambil cuaca Jakarta Pusat
    data = weather.get_weather("Jakarta Pusat")
    print(data)
"""

import requests
from datetime import datetime
from config import WEATHER_API_URL, LOCATIONS, WEATHER_PARAMS
from database import TrafficDatabase


class WeatherAPI:
    """
    Kelas untuk ambil data cuaca dari Open-Meteo.
    """

    def __init__(self):
        self.api_url = WEATHER_API_URL
        self.locations = LOCATIONS
        self.db = TrafficDatabase()

    # ─────────────────────────────────────────
    # DECODE WEATHER CODE
    # ─────────────────────────────────────────
    def decode_weather_code(self, code: int) -> dict:
        """
        Decode weather code dari Open-Meteo ke deskripsi.
        
        Kode-kode dari API:
        0 = Clear sky (Cerah)
        1, 2, 3 = Mainly clear, partly cloudy, overcast
        45, 48 = Fog
        51, 53, 55 = Drizzle (Gerimis)
        61, 63, 65 = Rain (Hujan)
        66, 67 = Freezing rain
        71, 73, 75 = Snow
        77 = Snow grains
        80, 81, 82 = Rain showers
        85, 86 = Snow showers
        95 = Thunderstorm
        96, 99 = Thunderstorm with hail
        
        Return:
            dict: {"description": "...", "rain_category": "none/light/moderate/heavy/extreme"}
        """
        # Mapping kode ke deskripsi dan kategori hujan
        weather_map = {
            0:  {"description": "Cerah",              "rain_category": "none"},
            1:  {"description": "Cerah Sebagian",     "rain_category": "none"},
            2:  {"description": "Berawan Sebagian",   "rain_category": "none"},
            3:  {"description": "Mendung",            "rain_category": "none"},
            45: {"description": "Kabut",              "rain_category": "none"},
            48: {"description": "Kabut Tebal",        "rain_category": "none"},
            51: {"description": "Gerimis Ringan",     "rain_category": "light"},
            53: {"description": "Gerimis Sedang",     "rain_category": "light"},
            55: {"description": "Gerimis Lebat",      "rain_category": "moderate"},
            61: {"description": "Hujan Ringan",       "rain_category": "light"},
            63: {"description": "Hujan Sedang",       "rain_category": "moderate"},
            65: {"description": "Hujan Lebat",        "rain_category": "heavy"},
            66: {"description": "Hujan Es Ringan",    "rain_category": "moderate"},
            67: {"description": "Hujan Es Lebat",     "rain_category": "heavy"},
            71: {"description": "Salju Ringan",       "rain_category": "light"},
            73: {"description": "Salju Sedang",       "rain_category": "moderate"},
            75: {"description": "Salju Lebat",        "rain_category": "heavy"},
            80: {"description": "Hujan Singkat",      "rain_category": "light"},
            81: {"description": "Hujan Singkat Sedang","rain_category": "moderate"},
            82: {"description": "Hujan Singkat Lebat","rain_category": "heavy"},
            95: {"description": "Petir",              "rain_category": "extreme"},
            96: {"description": "Petir + Es",         "rain_category": "extreme"},
            99: {"description": "Petir + Es Lebat",   "rain_category": "extreme"},
        }

        # Kalau kode tidak ditemukan, default ke "Unknown"
        return weather_map.get(code, {"description": "Unknown", "rain_category": "none"})

    # ─────────────────────────────────────────
    # FETCH CUACA 1 LOKASI
    # ─────────────────────────────────────────
    def get_weather(self, location: str) -> dict:
        """
        Ambil data cuaca untuk 1 lokasi.
        
        Parameter:
            location = nama lokasi, contoh: "Jakarta Pusat"
        
        Return:
            dict berisi data cuaca, atau None kalau error
        
        Contoh return:
            {
                "location": "Jakarta Pusat",
                "temperature": 28.5,
                "precipitation": 2.1,
                "windspeed": 12.3,
                "weather_code": 61,
                "weather_desc": "Hujan Ringan",
                "rain_category": "light",
                "timestamp": "2026-01-22 10:30:00"
            }
        """
        # Cek apakah lokasi ada di config
        if location not in self.locations:
            print(f"❌ Lokasi '{location}' tidak ditemukan!")
            return None

        # Ambil koordinat
        coords = self.locations[location]

        # Buat parameter API
        params = WEATHER_PARAMS.copy()
        params["latitude"] = coords["lat"]
        params["longitude"] = coords["lon"]

        try:
            print(f"🌤️  Fetching cuaca untuk {location}...")

            # Kirim request ke Open-Meteo
            # timeout=10 → kalau lebih dari 10 detik, batal
            response = requests.get(self.api_url, params=params, timeout=10)

            # Cek apakah request berhasil (status 200 = OK)
            if response.status_code != 200:
                print(f"❌ API error: status {response.status_code}")
                return None

            # Parse response jadi dict Python
            data = response.json()

            # ── Ambil data dari response ──
            # current_weather = cuaca saat ini
            current = data.get("current_weather", {})

            # hourly = data per jam hari ini
            hourly = data.get("hourly", {})

            # Ambil precipitation (hujan) untuk jam sekarang
            # Cari index jam sekarang di hourly data
            current_hour = datetime.now().hour
            precipitation = 0.0

            if "precipitation" in hourly:
                # hourly["time"] = list waktu, cari yang sesuai jam sekarang
                times = hourly.get("time", [])
                for i, time_str in enumerate(times):
                    if datetime.fromisoformat(time_str).hour == current_hour:
                        precipitation = hourly["precipitation"][i]
                        break

            # Decode weather code
            weather_code = current.get("weathercode", 0)
            weather_info = self.decode_weather_code(weather_code)

            # Buat result dict
            result = {
                "location": location,
                "temperature": current.get("temperature", 0),
                "precipitation": precipitation,
                "windspeed": current.get("windspeed", 0),
                "weather_code": weather_code,
                "weather_desc": weather_info["description"],
                "rain_category": weather_info["rain_category"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            print(f"  ✅ {location}: {result['weather_desc']}, "
                  f"Suhu {result['temperature']}°C, "
                  f"Hujan {result['precipitation']}mm")

            return result

        except requests.exceptions.ConnectionError:
            print(f"❌ Tidak bisa konek ke internet! Cek koneksi.")
            return None
        except requests.exceptions.Timeout:
            print(f"❌ Request timeout! API lambat.")
            return None
        except Exception as e:
            print(f"❌ Error tak terduga: {e}")
            return None

    # ─────────────────────────────────────────
    # FETCH CUACA SEMUA LOKASI
    # ─────────────────────────────────────────
    def get_all_weather(self) -> list:
        """
        Ambil cuaca untuk SEMUA lokasi sekaligus.
        
        Return:
            list of dict (hasil dari get_weather per lokasi)
        """
        results = []
        print("\n🌍 Fetching cuaca semua lokasi Jakarta...")
        print("─" * 40)

        for location in self.locations:
            data = self.get_weather(location)
            if data:
                results.append(data)

        print("─" * 40)
        print(f"✅ Berhasil fetch {len(results)} lokasi\n")
        return results

    # ─────────────────────────────────────────
    # FETCH & SIMPAN KE DATABASE
    # ─────────────────────────────────────────
    def fetch_and_save(self) -> list:
        """
        Ambil cuaca semua lokasi dan simpan ke database.
        Ini yang dipanggil dari dashboard untuk real-time update.
        
        Return:
            list of dict (data cuaca yang berhasil disimpan)
        """
        # Fetch dari API
        weather_list = self.get_all_weather()

        # Simpan ke database satu per satu
        for weather in weather_list:
            self.db.insert_weather_data(weather)

        print(f"💾 Saved {len(weather_list)} weather records to database")
        return weather_list