import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime, timezone, timedelta
import pydeck as pdk
import plotly.express as px
import pyodbc
import smtplib
from email.mime.text import MIMEText          
from email.mime.multipart import MIMEMultipart  
import os
import warnings

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")
# ----------------------------
# Constants
# ----------------------------
SIM_DEFAULT_INTERVAL = 5
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
TRAFFIC_INCIDENTS = ["None", "Minor Accident", "Major Accident", "Vehicle Breakdown", "Road Construction", "Police Checkpoint"]

# Azure & Email Config
AZURE_SQL_CONN_STR = st.secrets.get("AZURE_SQL_CONN_STR") or os.getenv("AZURE_SQL_CONN_STR")
ALERT_EMAIL_FROM   = st.secrets.get("ALERT_EMAIL_FROM")   or os.getenv("ALERT_EMAIL_FROM")
ALERT_EMAIL_TO     = st.secrets.get("ALERT_EMAIL_TO")     or os.getenv("ALERT_EMAIL_TO")
ALERT_EMAIL_PASSWORD = st.secrets.get("ALERT_EMAIL_PASSWORD") or os.getenv("ALERT_EMAIL_PASSWORD")

if not AZURE_SQL_CONN_STR:
    st.error("AZURE_SQL_CONN_STR is missing! Add it to .streamlit/secrets.toml OR Codespaces secrets")
    st.stop()
# ONLY ONE TABLE IN AZURE SQL
TABLE_ALERTS = "TrafficAlerts"

# Auto-create table if it doesn't exist 
def ensure_table_exists():
    try:
        conn = pyodbc.connect(AZURE_SQL_CONN_STR)
        cursor = conn.cursor()
        cursor.execute("""
            IF OBJECT_ID('TrafficAlerts') IS NULL
            CREATE TABLE TrafficAlerts (
                Id INT IDENTITY(1,1) PRIMARY KEY,
                AlertTimestamp DATETIME2 DEFAULT GETDATE(),
                LocationName NVARCHAR(100),
                AlertType NVARCHAR(300),
                DetailsJSON NVARCHAR(MAX)
            )
        """)
        conn.commit()
        conn.close()
    except:
        pass

ensure_table_exists()   # ← prevents table missing error

# ----------------------------
# Helpers
# ----------------------------
def calculate_rush_hour_factor(dt=None):
    if dt is None: dt = datetime.now()
    hour = dt.hour
    if 7 <= hour <= 10: return 1.5
    elif 18 <= hour <= 21: return 1.4
    elif hour <= 6 or hour >= 22: return 0.4
    else: return 1.0

def generate_realistic_traffic_data(now=None):
    location = random.choice(LOCATIONS)
    if now is None: now = datetime.now(timezone.utc)
    rush_factor = calculate_rush_hour_factor(now.astimezone())
    cap = location["cap"]
    min_vehicles = max(5, int(cap * 0.3 * rush_factor))
    max_vehicles = min(cap, int(cap * 1.2 * rush_factor))
    vehicle_count = random.randint(min_vehicles, max_vehicles)
    if random.random() < 0.08: vehicle_count = int(min(cap * 1.5, vehicle_count * 1.8))

    vehicle_type = random.choice(VEHICLE_TYPES)
    if random.random() < 0.08:
        speed = random.uniform(5, 15) if random.random() < 0.6 else random.uniform(85, 110)
    else:
        base_speed = random.uniform(20, 80)
        adjusted_speed = base_speed * (0.8 if rush_factor > 1.0 else 1.2)
        speed = max(5, min(110, round(adjusted_speed, 1)))

    congestion_pct = round(vehicle_count / cap * 100, 2)
    incident = random.choice(TRAFFIC_INCIDENTS) if random.random() < 0.15 else "None"

    return {
        "Timestamp": now.isoformat(timespec='seconds'),
        "ts": now,
        "LocationID": location["id"],
        "LocationName": location["name"],
        "Latitude": float(location["lat"]),
        "Longitude": float(location["lon"]),
        "VehicleCount": int(vehicle_count),
        "AverageSpeedKMH": float(round(speed,2)),
        "DominantVehicleType": vehicle_type,
        "WeatherCondition": random.choice(["Clear", "Cloudy", "Rain", "Fog"]),
        "TrafficIncident": incident,
        "CongestionPercentage": float(congestion_pct),
    }

def detect_anomaly(event):
    alerts = []
    if event["AverageSpeedKMH"] < 10: alerts.append("Severe Congestion")
    if event["AverageSpeedKMH"] > 100: alerts.append("Unusual High Speed")
    if event["CongestionPercentage"] > 120: alerts.append("Over Capacity")
    if event["CongestionPercentage"] > 90: alerts.append("Critical Congestion")
    if event["TrafficIncident"] != "None": alerts.append(f"Incident: {event['TrafficIncident']}")
    return alerts

def save_alert_to_azure(event, alert_msg):
    try:
        conn = pyodbc.connect(AZURE_SQL_CONN_STR)
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {TABLE_ALERTS} (LocationName, AlertType, DetailsJSON, AlertTimestamp)
            VALUES (?, ?, ?, GETDATE())
        """, event['LocationName'], alert_msg, str(event))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to save alert: {e}")

def send_email_alert(alert_msg, event):
    if not all([ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_EMAIL_PASSWORD]):
        return
    try:
        msg = MIMEMultipart()   
        msg['From'] = ALERT_EMAIL_FROM
        msg['To'] = ALERT_EMAIL_TO
        msg['Subject'] = f"CAIRO TRAFFIC ALERT - {event['LocationName']}"
        body = f"""
        TRAFFIC ALERT
        Location: {event['LocationName']}
        Time: {event['Timestamp']}
        {alert_msg}
        Speed: {event['AverageSpeedKMH']} km/h | Congestion: {event['CongestionPercentage']}% | Vehicles: {event['VehicleCount']}
        """
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(ALERT_EMAIL_FROM, ALERT_EMAIL_PASSWORD)
        server.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO, msg.as_string())
        server.quit()
    except:
        pass

def load_alerts_from_azure():
    try:
        conn = pyodbc.connect(AZURE_SQL_CONN_STR)
        df = pd.read_sql(f"SELECT TOP 100 * FROM {TABLE_ALERTS} ORDER BY AlertTimestamp DESC", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# ----------------------------
# Streamlit App
# ----------------------------
st.set_page_config(page_title="Cairo Traffic Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("Cairo Traffic Monitoring System")
st.markdown("**Real-time dashboard • Only critical alerts saved to Azure SQL • Email notifications**")

with st.sidebar:
    st.header("Controls")
    interval = st.slider("Refresh (seconds)", 2, 10, 5)
    run = st.button("Start Live Simulation", type="primary")
    st.info("Kareem Mostafa: Alert System Developer")

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "running" not in st.session_state:
    st.session_state.running = False

if run:
    st.session_state.running = True

def append_event(e):
    row = pd.DataFrame([e])
    st.session_state.df = pd.concat([st.session_state.df.tail(MAX_EVENTS_KEEP-1), row], ignore_index=True)

# Main loop
if st.session_state.running:
    event = generate_realistic_traffic_data()
    append_event(event)
    anomalies = detect_anomaly(event)
    if anomalies:
        alert_msg = " | ".join(anomalies)
        save_alert_to_azure(event, alert_msg)
        send_email_alert(alert_msg, event)

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Map", "Analytics", "Alerts (from Azure)"])

with tab1:
    st.subheader("Live Overview")
    if st.session_state.df.empty:
        st.info("Click 'Start Live Simulation'")
    else:
        latest = st.session_state.df.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Location", latest["LocationName"])
        c2.metric("Vehicles", latest["VehicleCount"])
        c3.metric("Speed", f"{latest['AverageSpeedKMH']:.1f} km/h")
        c4.metric("Congestion", f"{latest['CongestionPercentage']:.1f}%")

with tab2:
    if not st.session_state.df.empty:
        latest_per_loc = st.session_state.df.sort_values("ts").groupby("LocationName").last().reset_index()
        midpoint = (latest_per_loc["Latitude"].mean(), latest_per_loc["Longitude"].mean())
        layer = pdk.Layer("ScatterplotLayer", data=latest_per_loc,
            get_position="[Longitude, Latitude]",
            get_fill_color="[255, 50, 50, 180]",
            get_radius="CongestionPercentage * 30",
            pickable=True)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(latitude=midpoint[0], longitude=midpoint[1], zoom=11)))

with tab3:
    if not st.session_state.df.empty:
        df = st.session_state.df.tail(200)
        st.line_chart(df.set_index("ts")[["AverageSpeedKMH", "CongestionPercentage"]])

with tab4:
    st.subheader("Real Alerts from Azure SQL")
    alerts_df = load_alerts_from_azure()
    if alerts_df.empty:
        st.success("No critical alerts yet — traffic is normal!")
    else:
        st.error(f"{len(alerts_df)} CRITICAL ALERTS IN DATABASE")
        st.dataframe(alerts_df, use_container_width=True)

if st.session_state.running:
    time.sleep(interval)
    st.rerun()
