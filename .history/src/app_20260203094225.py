"""
app.py
──────
File UTAMA — Streamlit Dashboard.
Ini yang dijalankan untuk membuka dashboard.

Cara jalankan:
    cd C:\bigdata-traffic\src
    streamlit run app.py

Streamlit akan otomatis buka browser ke:
    http://localhost:8501
"""

import sys
import os
import time
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# ── Tambah folder "src" ke path ──
# Agar bisa import file-file lain (config, database, dll)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import LOCATIONS
from database import TrafficDatabase
from weather_api import WeatherAPI
from traffic_engine import TrafficEngine
from analytics import TrafficAnalytics
from data_generator import DataGenerator

# ── Gunakan font yang lebih baik untuk chart ──
matplotlib.use("Agg")


# ═══════════════════════════════════════════════
# KONFIGURASI STREAMLIT
# ═══════════════════════════════════════════════
st.set_page_config(
    page_title="Big Data Traffic Jakarta",
    page_icon="🚗",
    layout="wide",          # Layout lebar
    initial_sidebar_state="expanded",
)

# ── CSS Custom ──
st.markdown("""
<style>
    /* Sidebar gelap */
    .css-1aumxhk {
        background-color: #1a1a2e;
        color: white;
    }
    /* Judul besar */
    h1 {
        color: #e94560;
        text-align: center;
    }
    /* Metric cards */
    .stMetric {
        background-color: #16213e;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #0f3460;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# INISIALISASI (Jalankan 1x)
# ═══════════════════════════════════════════════
def initialize():
    """
    Inisialisasi database dan generate data kalau belum ada.
    Pakai st.session_state untuk pastikan hanya jalan 1x.
    """
    if "initialized" not in st.session_state:
        db = TrafficDatabase()
        db.init_tables()

        # Cek apakah data historis sudah ada
        total = db.get_traffic_count()

        if total < 1000:
            # Belum ada data → generate
            with st.spinner("⏳ Generating historical data (ini cuma 1x, tunggu ~30 detik)..."):
                gen = DataGenerator()
                gen.generate_historical_data()

        st.session_state["initialized"] = True


# ═══════════════════════════════════════════════
# SIDEBAR — Navigasi & Kontrol
# ═══════════════════════════════════════════════
def render_sidebar():
    """Render sidebar dengan menu dan kontrol."""
    st.sidebar.markdown("## 🚗 Big Data Traffic Jakarta")
    st.sidebar.markdown("---")

    # Menu halaman
    pages = [
        "📊 Dashboard Utama",
        "🌤️  Cuaca Real-Time",
        "📈 Analisis Hourly",
        "🌧️  Korelasi Hujan",
        "📍 Perbandingan Lokasi",
        "🔮 Prediksi Traffic",
        "📋 Data Raw",
    ]

    selected_page = st.sidebar.radio("Pilih Halaman:", pages)

    st.sidebar.markdown("---")

    # Kontrol simulasi
    st.sidebar.markdown("### ⚙️ Kontrol")

    # Tombol refresh simulasi
    if st.sidebar.button("🔄 Refresh Simulasi", use_container_width=True):
        engine = TrafficEngine()
        engine.run_simulation_cycle()
        st.rerun()

    # Tombol refresh cuaca
    if st.sidebar.button("🌤️ Refresh Cuaca", use_container_width=True):
        weather = WeatherAPI()
        weather.fetch_and_save()
        st.rerun()

    # Pilih lokasi
    st.sidebar.markdown("### 📍 Pilih Lokasi")
    locations = list(LOCATIONS.keys())
    selected_location = st.sidebar.selectbox("Lokasi:", ["Semua"] + locations)

    st.sidebar.markdown("---")

    # Info sistem
    db = TrafficDatabase()
    st.sidebar.markdown("### 📊 Info Sistem")
    st.sidebar.text(f"Total Traffic Data: {db.get_traffic_count():,}")
    st.sidebar.text(f"Total Weather Data: {db.get_weather_count():,}")

    return selected_page, selected_location


# ═══════════════════════════════════════════════
# HALAMAN 1: DASHBOARD UTAMA
# ═══════════════════════════════════════════════
def page_dashboard():
    """Dashboard utama dengan overview semua data."""
    st.title("📊 Dashboard Utama — Traffic Jakarta")

    db = TrafficDatabase()
    analytics = TrafficAnalytics()

    # ── Row 1: Metric Cards ──
    stats = analytics.get_overall_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Total Data", f"{stats['total_records']:,}", help="Total baris data traffic")
    col2.metric("🚗 Avg Kendaraan", f"{stats['avg_vehicles']}", help="Rata-rata kendaraan")
    col3.metric("🏎️ Avg Kecepatan", f"{stats['avg_speed']} km/h", help="Rata-rata kecepatan")
    col4.metric("🔴 Max Kendaraan", f"{stats['max_vehicles']}", help="Kendaraan terbanyak")
    col5.metric("📍 Lokasi", f"{stats['total_locations']}", help="Jumlah lokasi")

    st.markdown("---")

    # ── Row 2: Status Per Lokasi ──
    st.subheader("🚦 Status Traffic Saat Ini")

    current_status = analytics.get_current_status()
    if not current_status.empty:
        cols = st.columns(len(LOCATIONS))
        for i, row in current_status.iterrows():
            with cols[i % len(LOCATIONS)]:
                # Warna berdasarkan kondisi
                color = "🟢" if row["condition"] == "Lancar" else \
                        "🟡" if row["condition"] == "Sedang" else \
                        "🟠" if row["condition"] == "Padat" else \
                        "🔴"
                st.markdown(f"""
                <div style="
                    border: 2px solid #{'22c55e' if row['condition']=='Lancar' else 'eab308' if row['condition']=='Sedang' else 'f97316' if row['condition']=='Padat' else 'ef4444'};
                    border-radius: 10px;
                    padding: 15px;
                    text-align: center;
                    background: #1e293b;
                    color: white;
                ">
                    <div style="font-size: 24px;">{color}</div>
                    <div style="font-weight: bold; margin: 5px 0;">{row['location']}</div>
                    <div style="color: #94a3b8;">{int(row['vehicle_count'])} kendaraan</div>
                    <div style="color: #94a3b8;">{row['speed_kmh']} km/h</div>
                    <div style="font-weight: bold;">{row['condition']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Row 3: Chart Hourly Pattern ──
    st.subheader("📈 Pattern Kendaraan Per Jam (24 Jam)")

    hourly = analytics.get_hourly_pattern()
    if not hourly.empty:
        fig, ax = plt.subplots(figsize=(14, 4))
        ax.bar(hourly["hour"], hourly["avg_vehicles"], color="#e94560", alpha=0.8)
        ax.set_xlabel("Jam")
        ax.set_ylabel("Rata-rata Kendaraan")
        ax.set_title("Jumlah Kendaraan Rata-rata Per Jam")
        ax.set_xticks(range(0, 24))
        ax.set_xticklabels([f"{h}:00" for h in range(0, 24)], rotation=45, fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        ax.set_facecolor("#1a1a2e")
        fig.patch.set_facecolor("#16213e")
        ax.tick_params(colors="white")
        ax.title.set_color("white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # ── Row 4: Top Kemacetan ──
    st.markdown("---")
    st.subheader("🔴 Top 10 Kemacetan Terbesar")
    top = analytics.get_top_congestion(10)
    if not top.empty:
        st.dataframe(top, use_container_width=True)


# ═══════════════════════════════════════════════
# HALAMAN 2: CUACA REAL-TIME
# ═══════════════════════════════════════════════
def page_weather():
    """Tampilkan data cuaca real-time dari Open-Meteo."""
    st.title("🌤️  Cuaca Real-Time Jakarta")

    db = TrafficDatabase()

    # Ambil cuaca terbaru
    weather_df = db.get_latest_weather()

    if weather_df.empty:
        st.warning("⚠️ Belum ada data cuaca. Klik 'Refresh Cuaca' di sidebar.")
        return

    # Tampilkan per lokasi
    cols = st.columns(len(weather_df))
    for i, row in weather_df.iterrows():
        with cols[i % len(weather_df)]:
            # Icon berdasarkan cuaca
            icon = "☀️" if row["rain_category"] == "none" else \
                   "🌦️" if row["rain_category"] == "light" else \
                   "🌧️" if row["rain_category"] == "moderate" else \
                   "⛈️"
            st.markdown(f"""
            <div style="
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 15px;
                text-align: center;
                background: #1e293b;
                color: white;
            ">
                <div style="font-size: 30px;">{icon}</div>
                <div style="font-weight: bold;">{row['location']}</div>
                <div>🌡️ {row['temperature']}°C</div>
                <div>💧 {row['precipitation']} mm</div>
                <div>💨 {row['windspeed']} km/h</div>
                <div style="color: #94a3b8;">{row['weather_desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Detail Data Cuaca")
    st.dataframe(weather_df, use_container_width=True)


# ═══════════════════════════════════════════════
# HALAMAN 3: ANALISIS HOURLY
# ═══════════════════════════════════════════════
def page_hourly_analysis(selected_location):
    """Analisis detail per jam."""
    st.title("📈 Analisis Traffic Per Jam")

    analytics = TrafficAnalytics()

    # Filter lokasi
    location = None if selected_location == "Semua" else selected_location
    label = "Semua Lokasi" if selected_location == "Semua" else selected_location

    hourly = analytics.get_hourly_pattern(location)

    if hourly.empty:
        st.warning("Tidak ada data")
        return

    # ── Chart 1: Kendaraan per Jam ──
    st.subheader(f"🚗 Kendaraan Per Jam — {label}")
    fig, ax = plt.subplots(figsize=(14, 4))
    bars = ax.bar(hourly["hour"], hourly["avg_vehicles"], color="#38bdf8", alpha=0.8)
    # Highlight jam puncak
    for bar, hour in zip(bars, hourly["hour"]):
        if 6 <= hour <= 8 or 16 <= hour <= 18:
            bar.set_color("#e94560")
    ax.set_xlabel("Jam")
    ax.set_ylabel("Rata-rata Kendaraan")
    ax.set_title("Pattern Kendaraan (Merah = Jam Puncak)")
    ax.set_xticks(range(0, 24))
    ax.set_xticklabels([f"{h}:00" for h in range(0, 24)], rotation=45, fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#16213e")
    ax.tick_params(colors="white")
    ax.title.set_color("white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # ── Chart 2: Kecepatan Per Jam ──
    st.subheader(f"🏎️ Kecepatan Rata-rata Per Jam — {label}")
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(hourly["hour"], hourly["avg_speed"], color="#4ade80", marker="o", linewidth=2)
    ax.fill_between(hourly["hour"], hourly["avg_speed"], alpha=0.2, color="#4ade80")
    ax.set_xlabel("Jam")
    ax.set_ylabel("Kecepatan (km/h)")
    ax.set_title("Kecepatan Rata-rata Per Jam")
    ax.set_xticks(range(0, 24))
    ax.set_xticklabels([f"{h}:00" for h in range(0, 24)], rotation=45, fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#16213e")
    ax.tick_params(colors="white")
    ax.title.set_color("white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # ── Tabel Detail ──
    st.subheader("📋 Tabel Detail Per Jam")
    st.dataframe(hourly, use_container_width=True)


# ═══════════════════════════════════════════════
# HALAMAN 4: KORELASI HUJAN
# ═══════════════════════════════════════════════
def page_rain_correlation():
    """Analisis korelasi hujan vs kemacetan."""
    st.title("🌧️  Korelasi Hujan vs Kemacetan")

    analytics = TrafficAnalytics()
    rain_data = analytics.get_rain_correlation()

    if "error" in rain_data:
        st.warning(rain_data["error"])
        return

    # ── Metric ──
    col1, col2 = st.columns(2)
    col1.metric(
        "📊 Korelasi",
        f"{rain_data['correlation_coefficient']}",
        help="Nilai korelasi Pearson (-1 hingga 1)"
    )
    col2.metric(
        "📝 Interpretasi",
        rain_data["interpretation"]
    )

    st.markdown("---")

    # ── Chart: Korelasi ──
    stats_df = rain_data["stats_by_category"]
    if not stats_df.empty:
        # Urutan kategori
        order = ["Tidak Hujan", "Hujan Ringan", "Hujan Sedang", "Hujan Lebat", "Hujan Ekstrem"]
        stats_df["rain_category"] = pd.Categorical(stats_df["rain_category"], categories=order, ordered=True)
        stats_df = stats_df.sort_values("rain_category")

        st.subheader("📊 Rata-rata Kendaraan Berdasarkan Kondisi Hujan")
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = ["#4ade80", "#fbbf24", "#fb923c", "#f87171", "#dc2626"]
        bars = ax.bar(stats_df["rain_category"].astype(str), stats_df["avg_vehicles"], color=colors[:len(stats_df)])
        ax.set_xlabel("Kategori Hujan")
        ax.set_ylabel("Rata-rata Kendaraan")
        ax.set_title("Pengaruh Hujan Terhadap Kemacetan")
        ax.grid(axis="y", alpha=0.3)
        ax.set_facecolor("#1a1a2e")
        fig.patch.set_facecolor("#16213e")
        ax.tick_params(colors="white")
        ax.title.set_color("white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        plt.xticks(rotation=15)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # ── Tabel ──
        st.subheader("📋 Detail Statistik")
        st.dataframe(stats_df, use_container_width=True)


# ═══════════════════════════════════════════════
# HALAMAN 5: PERBANDINGAN LOKASI
# ═══════════════════════════════════════════════
def page_location_comparison():
    """Bandingkan traffic antar lokasi."""
    st.title("📍 Perbandingan Traffic Antar Lokasi")

    analytics = TrafficAnalytics()
    comparison = analytics.get_location_comparison()

    if comparison.empty:
        st.warning("Tidak ada data")
        return

    # ── Chart ──
    st.subheader("🏙️ Rata-rata Kendaraan Per Lokasi")
    fig, ax = plt.subplots(figsize=(12, 5))
    colors = plt.cm.Set2(np.linspace(0, 1, len(comparison)))
    bars = ax.barh(comparison["location"], comparison["avg_vehicles"], color=colors)
    ax.set_xlabel("Rata-rata Kendaraan")
    ax.set_title("Perbandingan Kepadatan Traffic Antar Lokasi")
    ax.grid(axis="x", alpha=0.3)
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#16213e")
    ax.tick_params(colors="white")
    ax.title.set_color("white")
    ax.xaxis.label.set_color("white")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # ── Chart: Persentase Macet ──
    st.subheader("🔴 Persentase Kemacetan Per Lokasi")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(
        comparison["macet_pct"],
        labels=comparison["location"],
        autopct="%1.1f%%",
        colors=plt.cm.Set3(np.linspace(0, 1, len(comparison))),
        startangle=90
    )
    ax.set_title("Distribusi Kemacetan Per Lokasi", color="white")
    fig.patch.set_facecolor("#16213e")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # ── Tabel ──
    st.subheader("📋 Detail Perbandingan")
    st.dataframe(comparison, use_container_width=True)


# ═══════════════════════════════════════════════
# HALAMAN 6: PREDIKSI TRAFFIC
# ═══════════════════════════════════════════════
def page_prediction(selected_location):
    """Prediksi traffic di masa depan."""
    st.title("🔮 Prediksi Traffic")

    analytics = TrafficAnalytics()

    # Input
    col1, col2 = st.columns(2)
    locations = list(LOCATIONS.keys())
    location = col1.selectbox("Pilih Lokasi:", locations)
    target_hour = col2.selectbox("Pilih Jam:", [f"{h}:00" for h in range(24)])
    hour_num = int(target_hour.split(":")[0])

    # Prediksi
    st.markdown("---")
    prediction = analytics.predict_traffic(location, hour_num)

    if "error" in prediction:
        st.warning(prediction["error"])
        return

    # Tampilkan hasil
    col1, col2, col3 = st.columns(3)
    col1.metric("🔽 Min Prediksi", f"{prediction['predicted_vehicles_min']} kendaraan")
    col2.metric("📊 Avg Prediksi", f"{prediction['predicted_vehicles_avg']} kendaraan")
    col3.metric("🔼 Max Prediksi", f"{prediction['predicted_vehicles_max']} kendaraan")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("🏎️ Kecepatan Prediksi", f"{prediction['predicted_speed']} km/h")
    col2.metric("🚦 Kondisi Prediksi", prediction["predicted_condition"])
    col3.metric("📈 Confidence", prediction["confidence"])

    st.markdown(f"\n📝 Prediksi berbasis dari **{prediction['samples_used']}** data historis.")


# ═══════════════════════════════════════════════
# HALAMAN 7: DATA RAW
# ═══════════════════════════════════════════════
def page_raw_data(selected_location):
    """Tampilkan data mentah dari database."""
    st.title("📋 Data Raw")

    db = TrafficDatabase()

    tab1, tab2 = st.tabs(["🚗 Traffic Data", "🌤️ Weather Data"])

    with tab1:
        if selected_location == "Semua":
            df = db.get_all_traffic_data()
        else:
            df = db.get_traffic_by_location(selected_location)

        st.metric("Total Baris", f"{len(df):,}")
        st.dataframe(df.head(100), use_container_width=True)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="traffic_data.csv",
            mime="text/csv",
        )

    with tab2:
        weather_df = db.get_all_weather_data()
        st.metric("Total Baris", f"{len(weather_df):,}")
        st.dataframe(weather_df.head(100), use_container_width=True)

        csv = weather_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="weather_data.csv",
            mime="text/csv",
        )


# ═══════════════════════════════════════════════
# MAIN — Entry Point
# ═══════════════════════════════════════════════
def main():
    """
    Main function — titik awal aplikasi.
    1. Initialize database
    2. Render sidebar
    3. Render halaman yang dipilih
    """
    # Step 1: Inisialisasi
    initialize()

    # Step 2: Sidebar
    selected_page, selected_location = render_sidebar()

    # Step 3: Render halaman berdasarkan pilihan
    if selected_page == "📊 Dashboard Utama":
        page_dashboard()

    elif selected_page == "🌤️  Cuaca Real-Time":
        page_weather()

    elif selected_page == "📈 Analisis Hourly":
        page_hourly_analysis(selected_location)

    elif selected_page == "🌧️  Korelasi Hujan":
        page_rain_correlation()

    elif selected_page == "📍 Perbandingan Lokasi":
        page_location_comparison()

    elif selected_page == "🔮 Prediksi Traffic":
        page_prediction(selected_location)

    elif selected_page == "📋 Data Raw":
        page_raw_data(selected_location)


 if __name__ == "__main__":
    main()