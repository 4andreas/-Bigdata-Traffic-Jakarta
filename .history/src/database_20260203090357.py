"""
database.py
───────────
Semua logika database ada di sini.
Pakai SQLite yang sudah built-in di Python (tidak perlu install tambahan).

SQLite = database dalam bentuk FILE (.db)
Keuntungan: tidak perlu server, tidak perlu install MySQL/Postgres
Cocok untuk: laptop lokal, tugas kuliah, prototype

Cara pakai:
    from database import TrafficDatabase
    db = TrafficDatabase()
    db.init_tables()
"""

import sqlite3
import pandas as pd
from config import DATABASE_PATH


class TrafficDatabase:
    """
    Kelas untuk mengelola semua operasi database.
    
    Tiap kali mau akses database, buat instance:
        db = TrafficDatabase()
    
    Lalu pakai method-method di bawah.
    """

    def __init__(self):
        """
        __init__ = constructor, jalan saat pertama kali class di-create.
        Simpan path database dan pastikan folder ada.
        """
        self.db_path = DATABASE_PATH
        print(f"📁 Database path: {self.db_path}")

    def get_connection(self):
        """
        Buat koneksi ke database SQLite.
        check_same_thread=False → biar bisa diakses dari berbagai thread
        """
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # Row factory → hasilnya bisa diakses seperti dictionary
        conn.row_factory = sqlite3.Row
        return conn

    # ─────────────────────────────────────────
    # CREATE TABLES
    # ─────────────────────────────────────────
    def init_tables(self):
        """
        Buat semua tabel di database.
        IF NOT EXISTS → kalau tabel sudah ada, tidak error.
        
        Tabel yang dibuat:
        1. traffic_data    → data traffic real-time & historis
        2. weather_data    → data cuaca dari API
        3. traffic_analysis → hasil analisis
        """
        print("🗄️  Initializing database tables...")
        
        conn = self.get_connection()
        cursor = conn.cursor()

        # ── Tabel 1: traffic_data ──
        # Simpan semua data traffic (historis + real-time)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_data (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,          -- Waktu (format: 2026-01-22 07:00:00)
                location    TEXT NOT NULL,          -- Nama lokasi (Jakarta Pusat, dst)
                vehicle_count INTEGER NOT NULL,    -- Jumlah kendaraan
                condition   TEXT NOT NULL,          -- Kondisi traffic (Lancar, Padat, Macet)
                speed_kmh   REAL,                  -- Kecepatan rata-rata (km/h)
                hour        INTEGER,               -- Jam (0-23), untuk analisis
                is_peak     INTEGER DEFAULT 0,     -- 1 = jam puncak, 0 = bukan
                rain_factor REAL DEFAULT 1.0,      -- Pengaruh hujan (1.0 = normal)
                data_source TEXT DEFAULT 'simulated' -- Sumber data
            )
        """)

        # ── Tabel 2: weather_data ──
        # Simpan data cuaca dari Open-Meteo API
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_data (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT NOT NULL,         -- Waktu pengambilan data
                location        TEXT NOT NULL,         -- Lokasi
                temperature     REAL,                  -- Suhu (°C)
                precipitation   REAL,                  -- Hujan (mm)
                windspeed       REAL,                  -- Kecepatan angin (km/h)
                weather_code    INTEGER,               -- Kode cuaca dari API
                weather_desc    TEXT,                  -- Deskripsi cuaca (Cerah, Hujan, dst)
                rain_category   TEXT DEFAULT 'none'    -- Kategori hujan (none/light/moderate/heavy)
            )
        """)

        # ── Tabel 3: traffic_analysis ──
        # Simpan hasil analisis yang sudah dihitung
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_analysis (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_date   TEXT NOT NULL,         -- Tanggal analisis
                location        TEXT NOT NULL,         -- Lokasi
                avg_vehicles    REAL,                  -- Rata-rata kendaraan
                max_vehicles    INTEGER,               -- Maksimum kendaraan
                min_vehicles    INTEGER,               -- Minimum kendaraan
                avg_speed       REAL,                  -- Rata-rata kecepatan
                peak_hour       INTEGER,               -- Jam paling padat
                rain_correlation REAL,                 -- Korelasi hujan vs macet
                total_records   INTEGER                -- Total data yang dianalisis
            )
        """)

        conn.commit()   # Simpan perubahan
        conn.close()    # Tutup koneksi
        print("✅ Tables created successfully!")

    # ─────────────────────────────────────────
    # INSERT DATA
    # ─────────────────────────────────────────
    def insert_traffic_data(self, records: list):
        """
        Insert banyak data traffic sekaligus.
        
        Parameter:
            records = list of dict, contoh:
            [
                {
                    "timestamp": "2026-01-22 07:00:00",
                    "location": "Jakarta Pusat",
                    "vehicle_count": 350,
                    "condition": "Padat",
                    "speed_kmh": 25.5,
                    "hour": 7,
                    "is_peak": 1,
                    "rain_factor": 1.3,
                    "data_source": "simulated"
                },
                ...
            ]
        """
        if not records:
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        # executemany = insert banyak baris sekaligus (lebih cepat)
        cursor.executemany("""
            INSERT INTO traffic_data 
            (timestamp, location, vehicle_count, condition, speed_kmh, 
             hour, is_peak, rain_factor, data_source)
            VALUES 
            (:timestamp, :location, :vehicle_count, :condition, :speed_kmh,
             :hour, :is_peak, :rain_factor, :data_source)
        """, records)

        conn.commit()
        conn.close()
        print(f"✅ Inserted {len(records)} traffic records")

    def insert_weather_data(self, record: dict):
        """
        Insert 1 data cuaca.
        
        Parameter:
            record = dict, contoh:
            {
                "timestamp": "2026-01-22 07:00:00",
                "location": "Jakarta Pusat",
                "temperature": 28.5,
                "precipitation": 2.1,
                "windspeed": 12.3,
                "weather_code": 61,
                "weather_desc": "Hujan Ringan",
                "rain_category": "light"
            }
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO weather_data 
            (timestamp, location, temperature, precipitation, windspeed,
             weather_code, weather_desc, rain_category)
            VALUES 
            (:timestamp, :location, :temperature, :precipitation, :windspeed,
             :weather_code, :weather_desc, :rain_category)
        """, record)

        conn.commit()
        conn.close()

    def insert_analysis(self, record: dict):
        """Insert hasil analisis."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO traffic_analysis 
            (analysis_date, location, avg_vehicles, max_vehicles, min_vehicles,
             avg_speed, peak_hour, rain_correlation, total_records)
            VALUES 
            (:analysis_date, :location, :avg_vehicles, :max_vehicles, :min_vehicles,
             :avg_speed, :peak_hour, :rain_correlation, :total_records)
        """, record)

        conn.commit()
        conn.close()

    # ─────────────────────────────────────────
    # SELECT / QUERY DATA
    # ─────────────────────────────────────────
    def get_all_traffic_data(self) -> pd.DataFrame:
        """
        Ambil SEMUA data traffic.
        Hasilnya langsung jadi pandas DataFrame.
        """
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM traffic_data ORDER BY timestamp DESC", conn)
        conn.close()
        return df

    def get_traffic_by_location(self, location: str) -> pd.DataFrame:
        """Ambil data traffic untuk 1 lokasi tertentu."""
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM traffic_data WHERE location = ? ORDER BY timestamp DESC",
            conn,
            params=(location,)
        )
        conn.close()
        return df

    def get_traffic_by_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Ambil data traffic dalam rentang tanggal.
        Format: "2026-01-01" sampai "2026-01-22"
        """
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM traffic_data WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
            conn,
            params=(start_date, end_date)
        )
        conn.close()
        return df

    def get_latest_traffic(self, limit: int = 10) -> pd.DataFrame:
        """Ambil data traffic terbaru (default 10 baris)."""
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM traffic_data ORDER BY timestamp DESC LIMIT ?",
            conn,
            params=(limit,)
        )
        conn.close()
        return df

    def get_all_weather_data(self) -> pd.DataFrame:
        """Ambil semua data cuaca."""
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM weather_data ORDER BY timestamp DESC", conn)
        conn.close()
        return df

    def get_latest_weather(self) -> pd.DataFrame:
        """Ambil data cuaca terbaru per lokasi."""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT * FROM weather_data 
            WHERE id IN (
                SELECT MAX(id) FROM weather_data GROUP BY location
            )
            ORDER BY location
        """, conn)
        conn.close()
        return df

    def get_traffic_count(self) -> int:
        """Hitung total baris data traffic."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM traffic_data")
        result = cursor.fetchone()
        conn.close()
        return result["total"]

    def get_weather_count(self) -> int:
        """Hitung total baris data cuaca."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM weather_data")
        result = cursor.fetchone()
        conn.close()
        return result["total"]

    def get_hourly_avg(self, location: str = None) -> pd.DataFrame:
        """
        Hitung rata-rata kendaraan per jam.
        Berguna untuk lihat pattern jam puncak.
        """
        conn = self.get_connection()
        query = """
            SELECT 
                hour,
                AVG(vehicle_count) as avg_vehicles,
                AVG(speed_kmh) as avg_speed,
                COUNT(*) as total_records
            FROM traffic_data
        """
        if location:
            query += " WHERE location = ?"
            df = pd.read_sql_query(query + " GROUP BY hour ORDER BY hour", conn, params=(location,))
        else:
            df = pd.read_sql_query(query + " GROUP BY hour ORDER BY hour", conn)
        
        conn.close()
        return df

    def clear_all_data(self):
        """Hapus semua data (untuk reset). Hati-hati pakai ini!"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM traffic_data")
        cursor.execute("DELETE FROM weather_data")
        cursor.execute("DELETE FROM traffic_analysis")
        conn.commit()
        conn.close()
        print("🗑️  All data cleared!")