import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timezone, timedelta
import pydeck as pdk
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ----------------------------
# Settings / Constants
# ----------------------------
SIM_DEFAULT_INTERVAL = 1  # seconds
MAX_EVENTS_KEEP = 5000

LOCATIONS = [
    {"id": "LOC001", "name": "Tahrir Square", "lat": 30.0444, "lon": 31.2357, "cap": 120},
    {"id": "LOC002", "name": "Ramses Square", "lat": 30.0626, "lon": 31.2497, "cap": 150},
    {"id": "LOC003", "name": "6th October Bridge", "lat": 30.0626, "lon": 31.2444, "cap": 100},
    {"id": "LOC004", "name": "Nasr City - Abbas El Akkad", "lat": 30.0515, "lon": 31.3381, "cap": 80},
    {"id": "LOC005", "name": "Heliopolis - Uruba Street", "lat": 30.0808, "lon": 31.3239, "cap": 90},
    {"id": "LOC006", "name": "Maadi Corniche", "lat": 29.9594, "lon": 31.2584, "cap": 60},
    {"id": "LOC007", "name": "Ahmed Orabi Square", "lat": 30.0618, "lon": 31.2001, "cap": 110},
]

VEHICLE_TYPES = ["Car", "Taxi", "Bus", "Microbus", "Truck", "Motorcycle", "Delivery Van"]
WEATHER_CONDITIONS = ["Clear", "Cloudy", "Light Rain", "Heavy Rain", "Foggy", "Sandstorm"]
TRAFFIC_INCIDENTS = ["None", "Minor Accident", "Major Accident", "Vehicle Breakdown", "Road Construction", "Police Checkpoint"]

# ----------------------------
# Helpers
# ----------------------------
def calculate_rush_hour_factor(dt=None):
    if dt is None:
        dt = datetime.now()
    hour = dt.hour
    if 7 <= hour <= 10:
        return 1.5
    elif 18 <= hour <= 21:
        return 1.4
    elif hour <= 6 or hour >= 22:
        return 0.4
    else:
        return 1.0

def generate_realistic_traffic_data(now=None):
    location = random.choice(LOCATIONS)
    if now is None:
        now = datetime.now(timezone.utc)
    rush_factor = calculate_rush_hour_factor(now.astimezone())
    cap = location["cap"]
    min_vehicles = max(5, int(cap * 0.3 * rush_factor))
    max_vehicles = min(cap, int(cap * 1.2 * rush_factor))
    vehicle_count = random.randint(min_vehicles, max_vehicles)

    if random.random() < 0.05:
        vehicle_count = int(min(cap * 1.5, vehicle_count * 1.8))

    vehicle_type = random.choice(VEHICLE_TYPES)
    if random.random() < 0.05:
        if random.random() < 0.5:
            speed = random.uniform(5, 15)
        else:
            speed = random.uniform(85, 110)
    else:
        base_speed = random.uniform(20, 80)
        adjusted_speed = base_speed * (0.8 if rush_factor > 1.0 else 1.2)
        speed = max(5, min(110, round(adjusted_speed, 1)))

    congestion_pct = round(vehicle_count / cap * 100, 2)
    incident = random.choice(TRAFFIC_INCIDENTS) if random.random() < 0.1 else "None"

    event = {
        "Timestamp": now.isoformat(timespec='seconds'),
        "ts": now,
        "LocationID": location["id"],
        "LocationName": location["name"],
        "Latitude": float(location["lat"]),
        "Longitude": float(location["lon"]),
        "VehicleCount": int(vehicle_count),
        "AverageSpeedKMH": float(round(speed,2)),
        "DominantVehicleType": vehicle_type,
        "WeatherCondition": random.choice(WEATHER_CONDITIONS),
        "TrafficIncident": incident,
        "CongestionPercentage": float(congestion_pct),
        "IsRushHour": rush_factor > 1.0,
        "RushFactor": float(round(rush_factor,2))
    }
    return event

def detect_anomaly(event):
    alerts = []
    if event["AverageSpeedKMH"] < 10:
        alerts.append("Low speed")
    if event["AverageSpeedKMH"] > 100:
        alerts.append("High speed")
    if event["CongestionPercentage"] > 120:
        alerts.append("Over capacity")
    elif event["CongestionPercentage"] > 85:
        alerts.append("High congestion")
    if event["TrafficIncident"] != "None":
        alerts.append(f"Incident: {event['TrafficIncident']}")
    return alerts

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Cairo Traffic Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("🚦 Cairo Traffic Dashboard")
st.markdown("Real-time simulator — Cairo traffic (Map, Analytics, Alerts).")

with st.sidebar:
    st.header("Controls")
    interval = st.slider("Refresh interval (seconds)", 1, 5, value=SIM_DEFAULT_INTERVAL)
    run_sim = st.button("Start / Resume")
    stop_sim = st.button("Stop")
    reset_data = st.button("Reset Data")
    st.markdown("---")
    st.markdown("Display Tabs")
    show_overview = st.checkbox("Overview", True)
    show_map = st.checkbox("Map", True)
    show_analytics = st.checkbox("Analytics", True)
    show_alerts = st.checkbox("Alerts", True)

if "df" not in st.session_state: st.session_state.df = pd.DataFrame()
if "running" not in st.session_state: st.session_state.running = False
if "alerts" not in st.session_state: st.session_state.alerts = []

if reset_data:
    st.session_state.df = pd.DataFrame()
    st.session_state.alerts = []
    st.success("Data reset.")
if run_sim: st.session_state.running = True
if stop_sim: st.session_state.running = False

# ----------------------------
# Local Simulator with Autorefresh
# ----------------------------
if st.session_state.running:
    ev = generate_realistic_traffic_data()
    df = st.session_state.df
    st.session_state.df = pd.concat([df, pd.DataFrame([ev])], ignore_index=True)
    if len(st.session_state.df) > MAX_EVENTS_KEEP:
        st.session_state.df = st.session_state.df.iloc[-MAX_EVENTS_KEEP:].reset_index(drop=True)

    detected = detect_anomaly(ev)
    if detected:
        st.session_state.alerts.append({
            "timestamp": ev["Timestamp"],
            "location": ev["LocationName"],
            "event": ", ".join(detected),
            "raw": ev
        })
        for alert_text in detected:
            st.toast(f"⚠️ {ev['LocationName']}: {alert_text}", icon="⚠️")

    # Autorefresh every interval seconds
    st_autorefresh(interval=interval*1000, key="traffic_timer")

# ----------------------------
# Tabs (Overview / Map / Analytics / Alerts)
# ----------------------------
tabs = []
if show_overview: tabs.append("Overview")
if show_map: tabs.append("Map")
if show_analytics: tabs.append("Analytics")
if show_alerts: tabs.append("Alerts")

tab_objs = st.tabs(tabs) if tabs else []

# ---------- Overview ----------
if show_overview:
    tab = tab_objs[tabs.index("Overview")]
    with tab:
        st.subheader("Overview — Live Snapshot")
        df = st.session_state.df
        if df.empty:
            st.info("No data yet. Click **Start / Resume**.")
        else:
            latest = df.iloc[-1]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Events", len(df))
            now = datetime.now(timezone.utc)
            recent = df[pd.to_datetime(df["ts"]) >= now - timedelta(minutes=5)]
            col2.metric("Events (last 5m)", len(recent))
            col3.metric("Avg Speed (last 5m)", round(recent["AverageSpeedKMH"].mean() if not recent.empty else latest["AverageSpeedKMH"],2))
            col4.metric("Avg Congestion (last 5m %)", round(recent["CongestionPercentage"].mean() if not recent.empty else latest["CongestionPercentage"],2))
            st.json({
                "time": latest["Timestamp"],
                "location": latest["LocationName"],
                "vehicles": latest["VehicleCount"],
                "speed": latest["AverageSpeedKMH"],
                "congestion%": latest["CongestionPercentage"],
                "incident": latest["TrafficIncident"]
            })

# ---------- Map ----------
if show_map:
    tab = tab_objs[tabs.index("Map")]
    with tab:
        st.subheader("Map")
        df = st.session_state.df
        if df.empty:
            st.info("No location points yet.")
        else:
            latest_per_loc = df.sort_values("ts").groupby("LocationID").last().reset_index()
            latest_per_loc["color_score"] = latest_per_loc["CongestionPercentage"]
            midpoint = (latest_per_loc["Latitude"].mean(), latest_per_loc["Longitude"].mean())
            
            # Create color mapping function instead of inline expression
            def get_color(congestion_pct):
                intensity = min(255, int(congestion_pct * 2.5))
                return [intensity, 50, 150, 200]
            
            latest_per_loc["fill_color"] = latest_per_loc["CongestionPercentage"].apply(get_color)
            
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=latest_per_loc,
                get_position='[Longitude, Latitude]',
                get_fill_color='fill_color',  # Use pre-computed column instead of expression
                get_radius='(CongestionPercentage+5) * 20',
                pickable=True,
                auto_highlight=True
            )
            view_state = pdk.ViewState(latitude=midpoint[0], longitude=midpoint[1], zoom=11, pitch=30)
            r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text":"{LocationName}\nCongestion: {CongestionPercentage}%\nVehicles: {VehicleCount}"})
            st.pydeck_chart(r)

# ---------- Analytics ----------
if show_analytics:
    tab = tab_objs[tabs.index("Analytics")]
    with tab:
        st.subheader("Analytics")
        df = st.session_state.df
        if df.empty:
            st.info("No data yet.")
        else:
            window = st.radio("Time window", ["Last 5 minutes", "Last 1 hour", "Last 24 hours", "All"], index=0, horizontal=True)
            now = datetime.now(timezone.utc)
            if window == "Last 5 minutes": cutoff = now - timedelta(minutes=5)
            elif window == "Last 1 hour": cutoff = now - timedelta(hours=1)
            elif window == "Last 24 hours": cutoff = now - timedelta(hours=24)
            else: cutoff = df["ts"].min()
            filtered = df[pd.to_datetime(df["ts"]) >= cutoff]
            if not filtered.empty:
                st.plotly_chart(px.line(filtered, x="ts", y="VehicleCount", title="VehicleCount"), use_container_width=True)
                st.plotly_chart(px.line(filtered, x="ts", y="AverageSpeedKMH", title="AverageSpeedKMH"), use_container_width=True)
                vdist = filtered["DominantVehicleType"].value_counts().reset_index()
                vdist.columns = ["VehicleType","Count"]
                st.plotly_chart(px.pie(vdist, names="VehicleType", values="Count", title="Vehicle types"), use_container_width=True)
                toploc = filtered.groupby("LocationName")["CongestionPercentage"].mean().sort_values(ascending=False).reset_index()
                st.dataframe(toploc.head(10))

# ---------- Alerts ----------
if show_alerts:
    tab = tab_objs[tabs.index("Alerts")]
    with tab:
        st.subheader("Alerts & Anomalies")
        alerts_df = pd.DataFrame(st.session_state.alerts)
        if alerts_df.empty:
            st.info("No alerts detected yet.")
        else:
            st.dataframe(alerts_df.sort_values("timestamp", ascending=False).reset_index(drop=True))
            for idx, row in alerts_df.iterrows():
                st.toast(f"⚠️ {row['location']}: {row['event']}", icon="⚠️")
            alerts_df["type_simple"] = alerts_df["event"].apply(lambda s: s.split(",")[0] if isinstance(s,str) else s)
            st.bar_chart(alerts_df["type_simple"].value_counts())

st.markdown("---")
st.caption("Local Simulator running — live traffic events with Alerts popup.")