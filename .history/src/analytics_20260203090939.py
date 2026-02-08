"""
analytics.py
────────────
Semua logika analisis data ada di sini.

Analisis yang tersedia:
1. Rata-rata kendaraan per jam (pattern jam puncak)
2. Korelasi hujan vs kemacetan
3. Perbandingan traffic antar lokasi
4. Prediksi traffic jam berikutnya (simple)
5. Statistik umum (total data, max, min, avg)
6. Analisis hari kerja vs weekend

Cara pakai:
    from analytics import TrafficAnalytics
    analytics = TrafficAnalytics()
    
    stats = analytics.get_overall_stats()
    hourly = analytics.get_hourly_pattern()
"""

import pandas as pd
import numpy as np
from database import TrafficDatabase
from config import LOCATIONS


class TrafficAnalytics:
    """
    Kelas untuk semua analisis data traffic.
    """

    def __init__(self):
        self.db = TrafficDatabase()

    # ─────────────────────────────────────────
    # 1. STATISTIK UMUM
    # ─────────────────────────────────────────
    def get_overall_stats(self) -> dict:
        """
        Dapatkan statistik umum dari seluruh data.
        
        Return:
            dict berisi: total_records, avg_vehicles, max_vehicles,
            min_vehicles, avg_speed, most_common_condition
        """
        df = self.db.get_all_traffic_data()

        if df.empty:
            return {"error": "Tidak ada data"}

        stats = {
            "total_records": len(df),
            "total_locations": df["location"].nunique(),
            "avg_vehicles": round(df["vehicle_count"].mean(), 1),
            "max_vehicles": int(df["vehicle_count"].max()),
            "min_vehicles": int(df["vehicle_count"].min()),
            "avg_speed": round(df["speed_kmh"].mean(), 1),
            "most_common_condition": df["condition"].mode()[0] if not df["condition"].mode().empty else "N/A",
            "peak_records": int(df["is_peak"].sum()),
            "rainy_records": int((df["rain_factor"] > 1.0).sum()),
        }

        return stats

    # ─────────────────────────────────────────
    # 2. PATTERN PER JAM
    # ─────────────────────────────────────────
    def get_hourly_pattern(self, location: str = None) -> pd.DataFrame:
        """
        Analisis pattern kendaraan per jam (0-23).
        Berguna untuk lihat jam puncak.
        
        Parameter:
            location = optional, filter per lokasi
        
        Return:
            DataFrame dengan kolom: hour, avg_vehicles, avg_speed, count
        """
        if location:
            df = self.db.get_traffic_by_location(location)
        else:
            df = self.db.get_all_traffic_data()

        if df.empty:
            return pd.DataFrame()

        # Group by jam, hitung rata-rata
        hourly = df.groupby("hour").agg(
            avg_vehicles=("vehicle_count", "mean"),
            max_vehicles=("vehicle_count", "max"),
            avg_speed=("speed_kmh", "mean"),
            count=("id", "count"),
        ).reset_index()

        # Round
        hourly["avg_vehicles"] = hourly["avg_vehicles"].round(1)
        hourly["avg_speed"] = hourly["avg_speed"].round(1)

        return hourly

    # ─────────────────────────────────────────
    # 3. KORELASI HUJAN VS KEMACETAN
    # ─────────────────────────────────────────
    def get_rain_correlation(self) -> dict:
        """
        Analisis korelasi antara hujan dan kemacetan.
        
        Logic:
        - Ambil semua data traffic
        - Group berdasarkan rain_factor
        - Hitung rata-rata kendaraan & kecepatan per kategori
        
        Return:
            dict berisi data korelasi per kategori hujan
        """
        df = self.db.get_all_traffic_data()

        if df.empty:
            return {"error": "Tidak ada data"}

        # Kategorisasi rain_factor
        def categorize_rain(factor):
            if factor <= 1.0:
                return "Tidak Hujan"
            elif factor <= 1.3:
                return "Hujan Ringan"
            elif factor <= 1.6:
                return "Hujan Sedang"
            elif factor <= 1.8:
                return "Hujan Lebat"
            else:
                return "Hujan Ekstrem"

        df["rain_category"] = df["rain_factor"].apply(categorize_rain)

        # Group dan hitung statistik
        rain_stats = df.groupby("rain_category").agg(
            avg_vehicles=("vehicle_count", "mean"),
            max_vehicles=("vehicle_count", "max"),
            avg_speed=("speed_kmh", "mean"),
            count=("id", "count"),
        ).reset_index()

        rain_stats["avg_vehicles"] = rain_stats["avg_vehicles"].round(1)
        rain_stats["avg_speed"] = rain_stats["avg_speed"].round(1)

        # Hitung correlation coefficient (Pearson)
        correlation = df["rain_factor"].corr(df["vehicle_count"])

        return {
            "correlation_coefficient": round(correlation, 3),
            "stats_by_category": rain_stats,
            "interpretation": self._interpret_correlation(correlation),
        }

    def _interpret_correlation(self, corr: float) -> str:
        """Interpretasi nilai korelasi."""
        if corr >= 0.7:
            return "Korelasi Kuat Positif: Hujan sangat mempengaruhi kemacetan"
        elif corr >= 0.4:
            return "Korelasi Sedang Positif: Hujan cukup mempengaruhi kemacetan"
        elif corr >= 0.2:
            return "Korelasi Lemah Positif: Hujan sedikit mempengaruhi kemacetan"
        else:
            return "Korelasi Sangat Lemah: Hujan tidak terlalu mempengaruhi"

    # ─────────────────────────────────────────
    # 4. PERBANDINGAN ANTAR LOKASI
    # ─────────────────────────────────────────
    def get_location_comparison(self) -> pd.DataFrame:
        """
        Bandingkan traffic antar lokasi.
        
        Return:
            DataFrame: location, avg_vehicles, max_vehicles, avg_speed, total_records
        """
        df = self.db.get_all_traffic_data()

        if df.empty:
            return pd.DataFrame()

        comparison = df.groupby("location").agg(
            avg_vehicles=("vehicle_count", "mean"),
            max_vehicles=("vehicle_count", "max"),
            min_vehicles=("vehicle_count", "min"),
            avg_speed=("speed_kmh", "mean"),
            total_records=("id", "count"),
            macet_count=("condition", lambda x: (x == "Macet").sum()),
        ).reset_index()

        comparison["avg_vehicles"] = comparison["avg_vehicles"].round(1)
        comparison["avg_speed"] = comparison["avg_speed"].round(1)

        # Tambah kolom: persentase kemacetan
        comparison["macet_pct"] = (
            comparison["macet_count"] / comparison["total_records"] * 100
        ).round(1)

        return comparison.sort_values("avg_vehicles", ascending=False)

    # ─────────────────────────────────────────
    # 5. PREDIKSI TRAFFIC
    # ─────────────────────────────────────────
    def predict_traffic(self, location: str, target_hour: int) -> dict:
        """
        Prediksi traffic untuk jam tertentu.
        Menggunakan rata-rata historis + faktor hujan.
        
        Simple prediction (tidak pakai ML berat):
        - Ambil rata-rata historis untuk jam tersebut
        - Adjust berdasarkan cuaca sekarang
        
        Parameter:
            location = nama lokasi
            target_hour = jam yang diprediksi (0-23)
        
        Return:
            dict berisi prediksi
        """
        df = self.db.get_traffic_by_location(location)

        if df.empty:
            return {"error": "Tidak ada data historis"}

        # Filter data untuk jam target
        df_hour = df[df["hour"] == target_hour]

        if df_hour.empty:
            return {"error": f"Tidak ada data untuk jam {target_hour}:00"}

        # Hitung rata-rata & standar deviasi
        avg_vehicles = df_hour["vehicle_count"].mean()
        std_vehicles = df_hour["vehicle_count"].std()
        avg_speed = df_hour["speed_kmh"].mean()

        # Prediksi range (avg ± 1 std)
        predicted_min = max(0, int(avg_vehicles - std_vehicles))
        predicted_max = int(avg_vehicles + std_vehicles)
        predicted_avg = int(avg_vehicles)

        # Tentukan kondisi prediksi
        from config import TRAFFIC_THRESHOLDS
        condition = "Lancar"
        for cond, (low, high) in TRAFFIC_THRESHOLDS.items():
            if low <= predicted_avg < high:
                condition = cond
                break

        return {
            "location": location,
            "target_hour": target_hour,
            "predicted_vehicles_min": predicted_min,
            "predicted_vehicles_avg": predicted_avg,
            "predicted_vehicles_max": predicted_max,
            "predicted_speed": round(avg_speed, 1),
            "predicted_condition": condition,
            "confidence": "Sedang (berbasis rata-rata historis)",
            "samples_used": len(df_hour),
        }

    # ─────────────────────────────────────────
    # 6. ANALISIS HARI KERJA VS WEEKEND
    # ─────────────────────────────────────────
    def get_weekday_vs_weekend(self) -> dict:
        """
        Bandingkan traffic di hari kerja vs weekend.
        
        Return:
            dict berisi perbandingan
        """
        df = self.db.get_all_traffic_data()

        if df.empty:
            return {"error": "Tidak ada data"}

        # Convert timestamp ke datetime
        df["datetime"] = pd.to_datetime(df["timestamp"])

        # Tambah kolom day_of_week (0=Senin, 6=Minggu)
        df["day_of_week"] = df["datetime"].dt.dayofweek

        # Pisah hari kerja (0-4) dan weekend (5-6)
        weekday = df[df["day_of_week"] < 5]
        weekend = df[df["day_of_week"] >= 5]

        result = {
            "weekday": {
                "label": "Hari Kerja (Sen-Jum)",
                "avg_vehicles": round(weekday["vehicle_count"].mean(), 1) if not weekday.empty else 0,
                "avg_speed": round(weekday["speed_kmh"].mean(), 1) if not weekday.empty else 0,
                "total_records": len(weekday),
            },
            "weekend": {
                "label": "Weekend (Sab-Min)",
                "avg_vehicles": round(weekend["vehicle_count"].mean(), 1) if not weekend.empty else 0,
                "avg_speed": round(weekend["speed_kmh"].mean(), 1) if not weekend.empty else 0,
                "total_records": len(weekend),
            },
        }

        return result

    # ─────────────────────────────────────────
    # 7. TOP KEMACETAN
    # ─────────────────────────────────────────
    def get_top_congestion(self, top_n: int = 10) -> pd.DataFrame:
        """
        Ambil N data traffic dengan kemacetan terbesar.
        
        Parameter:
            top_n = berapa baris teratas (default 10)
        
        Return:
            DataFrame: data traffic paling macet
        """
        df = self.db.get_all_traffic_data()

        if df.empty:
            return pd.DataFrame()

        # Sort berdasarkan vehicle_count, ambil top N
        top = df.nlargest(top_n, "vehicle_count")[
            ["timestamp", "location", "vehicle_count", "condition", "speed_kmh", "rain_factor"]
        ]

        return top.reset_index(drop=True)

    # ─────────────────────────────────────────
    # 8. KONDISI TRAFFIC SAAT INI (Per Lokasi)
    # ─────────────────────────────────────────
    def get_current_status(self) -> pd.DataFrame:
        """
        Ambil status traffic terbaru untuk setiap lokasi.
        
        Return:
            DataFrame: 1 baris per lokasi, data terbaru
        """
        df = self.db.get_all_traffic_data()

        if df.empty:
            return pd.DataFrame()

        # Convert timestamp
        df["datetime"] = pd.to_datetime(df["timestamp"])

        # Ambil yang terbaru per lokasi
        latest = df.sort_values("datetime").groupby("location").last().reset_index()

        return latest[["location", "vehicle_count", "condition", "speed_kmh", "rain_factor", "timestamp"]]