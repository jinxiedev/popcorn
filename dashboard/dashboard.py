import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from pathlib import Path

# ==============================
# KONFIGURASI
# ==============================

st.set_page_config(
    page_title="Air Quality Dashboard",
    page_icon="☁️",
    layout="wide"
)

sns.set_theme(style="darkgrid")

aqi_bins = [0, 12, 35.4, 55.4, 150.4, 250.4, float("inf")]
aqi_labels = [
    "Good",
    "Moderate",
    "Unhealthy for Sensitive Groups",
    "Unhealthy",
    "Very Unhealthy",
    "Hazardous"
]

# ==============================
# LOAD DATA
# ==============================

@st.cache_data
def load_data():
    BASE_DIR = Path(__file__).resolve().parent
    data_path = BASE_DIR / "main_data.csv"

    data = pd.read_csv(data_path)

    data["datetime"] = pd.to_datetime(data["datetime"])

    data["AQI_Category"] = pd.cut(
        data["PM2.5"],
        bins=aqi_bins,
        labels=aqi_labels,
        include_lowest=True
    )

    return data


df = load_data()

# ==============================
# SIDEBAR
# ==============================

st.sidebar.title("☁️ Air Quality Tracker")
st.sidebar.markdown("Silakan filter data di bawah ini:")

min_date = df["datetime"].min().date()
max_date = df["datetime"].max().date()

date_range = st.sidebar.date_input(
    "Rentang Waktu",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range[0]
    end_date = date_range[0]

# --- PERBAIKAN: Menambahkan Opsi "All Stations" ---

station_options = ["All Stations"] + list(df["station"].unique())

selected_stations = st.sidebar.multiselect(
    "Pilih Stasiun Pemantau:",
    options=station_options,
    default=["All Stations"] # Menjadikan "All Stations" sebagai pilihan default
)

# --- PERBAIKAN: Logika Filter Data ---

if "All Stations" in selected_stations:
    filtered_df = df[
        (df["datetime"].dt.date >= start_date) & 
        (df["datetime"].dt.date <= end_date)
    ].copy()

else:
    filtered_df = df[
        (df["datetime"].dt.date >= start_date) & 
        (df["datetime"].dt.date <= end_date) & 
        (df["station"].isin(selected_stations))
    ].copy()

# ==============================
# MAIN DASHBOARD
# ==============================
st.title("☁️ Air Quality Data Dashboard (Beijing)")
st.markdown(
"""
Dashboard ini menyajikan hasil analisis data kualitas udara
di berbagai stasiun pemantau Beijing dengan fokus pada **PM2.5**.
"""
)

# ==============================
# KPI
# ==============================

st.subheader("Ringkasan Data")

col1, col2, col3 = st.columns(3)

with col1:
    avg_pm25 = filtered_df["PM2.5"].mean()
    st.metric(
        "Rata-rata Konsentrasi PM2.5",
        f"{avg_pm25:.2f} µg/m³"
    )

with col2:
    max_pm25 = filtered_df["PM2.5"].max()
    st.metric(
        "Nilai PM2.5 Tertinggi",
        f"{max_pm25:.2f} µg/m³"
    )

with col3:
    if not filtered_df.empty:
        common_aqi = filtered_df["AQI_Category"].mode()[0]
    else:
        common_aqi = "N/A"

    st.metric(
        "Kategori AQI Terbanyak",
        common_aqi
    )

st.markdown("---")

# ==============================
# VISUALISASI
# ==============================

st.subheader("Tren dan Perbandingan Kualitas Udara")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:

    st.markdown("#### Tren Konsentrasi PM2.5 Bulanan")

    filtered_df["year_month"] = (
        filtered_df["datetime"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_pm25 = (
        filtered_df
        .groupby("year_month")["PM2.5"]
        .mean()
        .reset_index()
    )

    fig1, ax1 = plt.subplots(figsize=(10,6))

    sns.lineplot(
        data=monthly_pm25,
        x="year_month",
        y="PM2.5",
        marker="o",
        linewidth=2,
        ax=ax1
    )

    plt.xticks(rotation=45)

    st.pyplot(fig1)


with col_chart2:
    st.markdown("#### Perbandingan PM2.5 Antar Stasiun")

    station_pm25 = (
        filtered_df
        .groupby("station")["PM2.5"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig2, ax2 = plt.subplots(figsize=(10,6))

    # Pewarnaan batang chart
    if not station_pm25.empty:
        max_val = station_pm25['PM2.5'].max()
        min_val = station_pm25['PM2.5'].min()
        colors = ["#d32f2f" if val == max_val else "#388e3c" if val == min_val else "#d3d3d3" for val in station_pm25['PM2.5']]
    else:
        colors = "viridis"

    sns.barplot(
        data=station_pm25,
        x="PM2.5",
        y="station",
        palette=colors,
        ax=ax2
    )

    st.pyplot(fig2)

st.markdown("---")

# ==============================
# AQI DISTRIBUTION
# ==============================

st.subheader("Distribusi Kategori Kualitas Udara (AQI)")

fig3, ax3 = plt.subplots(figsize=(14,5))

sns.countplot(
    data=filtered_df,
    x="AQI_Category",
    order=aqi_labels,
    palette="magma",
    ax=ax3
)

st.pyplot(fig3)

with st.expander("Lihat Penjelasan Kategori AQI"):
    st.write("""
- Good (0–12)
- Moderate (12.1–35.4)
- Unhealthy for Sensitive Groups (35.5–55.4)
- Unhealthy (55.5–150.4)
- Very Unhealthy (150.5–250.4)
- Hazardous (>250.4)
""")

st.caption(
"Data source: PRSA Data (2013-2017) - Dicoding Academy"
)
