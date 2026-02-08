import sys
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import LOCATIONS
from database import TrafficDatabase
from weather_api import WeatherAPI
from traffic_engine import TrafficEngine
from analytics import TrafficAnalytics
from data_generator import DataGenerator

matplotlib.use("Agg")

st.set_page_config(
    page_title="Big Data Traffic Jakarta",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .css-1aumxhk { background-color: #1a1a2e; color: white; }
    h1 { color: #e94560; text-align: center; }
    .stMetric { background-color: #16213e; border-radius: 10px; padding: 15px; border: 1px solid #0f3460; }
</style>
""", unsafe_allow_html=True)


def initialize():
    if "initialized" not in st.session_state:
        db = TrafficDatabase()
        db.init_tables()
        total = db.get_traffic_count()
        if total < 1000:
            with st.spinner("⏳ Generating historical data..."):
                gen = DataGenerator()
                gen.generate_historical_data()
        st.session_state["initialized"] = True


def render_sidebar():
    st.sidebar.markdown("## 🚗 Big Data Traffic Jakarta")
    st.sidebar.markdown("---")

    pages = [
        "📊 Dashboard Utama",
        "🌤️ Cuaca Real-Time",
        "📋 Data Raw",
    ]

    selected_page = st.sidebar.radio("Pilih Halaman:", pages)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Kontrol")

    if st.sidebar.button("🔄 Refresh Simulasi", use_container_width=True):
        engine = TrafficEngine()
        engine.run_simulation_cycle()
        st.rerun()

    if st.sidebar.button("🌤️ Refresh Cuaca", use_container_width=True):
        weather = WeatherAPI()
        weather.fetch_and_save()
        st.rerun()

    st.sidebar.markdown("### 📍 Pilih Lokasi")
    locations = list(LOCATIONS.keys())
    selected_location = st.sidebar.selectbox("Lokasi:", ["Semua"] + locations)
    st.sidebar.markdown("---")

    db = TrafficDatabase()
    st.sidebar.markdown("### 📊 Info Sistem")
    st.sidebar.text(f"Total Traffic Data: {db.get_traffic_count():,}")
    st.sidebar.text(f"Total Weather Data: {db.get_weather_count():,}")

    return selected_page, selected_location


def page_dashboard():
    st.title("📊 Dashboard Utama — Traffic Jakarta")

    db = TrafficDatabase()
    analytics = TrafficAnalytics()
    stats = analytics.get_overall_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Total Data", f"{stats['total_records']:,}")
    col2.metric("🚗 Avg Kendaraan", f"{stats['avg_vehicles']}")
    col3.metric("🏎️ Avg Kecepatan", f"{stats['avg_speed']} km/h")
    col4.metric("🔴 Max Kendaraan", f"{stats['max_vehicles']}")
    col5.metric("📍 Lokasi", f"{stats['total_locations']}")

    st.markdown("---")
    st.subheader("🚦 Status Traffic Saat Ini")

    current_status = analytics.get_current_status()
    if not current_status.empty:
        cols = st.columns(len(LOCATIONS))
        for i, row in current_status.iterrows():
            with cols[i % len(LOCATIONS)]:
                color = "🟢" if row["condition"] == "Lancar" else \
                        "🟡" if row["condition"] == "Sedang" else \
                        "🟠" if row["condition"] == "Padat" else "🔴"
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

    st.markdown("---")
    st.subheader("🔴 Top 10 Kemacetan Terbesar")
    top = analytics.get_top_congestion(10)
    if not top.empty:
        st.dataframe(top, use_container_width=True)


def page_weather():
    st.title("🌤️ Cuaca Real-Time Jakarta")

    db = TrafficDatabase()
    weather_df = db.get_latest_weather()

    if weather_df.empty:
        st.warning("⚠️ Belum ada data cuaca. Klik 'Refresh Cuaca' di sidebar.")
        return

    cols = st.columns(len(weather_df))
    for i, row in weather_df.iterrows():
        with cols[i % len(weather_df)]:
            icon = "☀️" if row["rain_category"] == "none" else \
                   "🌦️" if row["rain_category"] == "light" else \
                   "🌧️" if row["rain_category"] == "moderate" else "⛈️"
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


def page_raw_data(selected_location):
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


def main():
    initialize()
    selected_page, selected_location = render_sidebar()

    if selected_page == "📊 Dashboard Utama":
        page_dashboard()
    elif selected_page == "🌤️ Cuaca Real-Time":
        page_weather()
    elif selected_page == "📋 Data Raw":
        page_raw_data(selected_location)


if __name__ == "__main__":
    main()