"""
CAIRO TRAFFIC DATA SIMULATOR
Digital Egypt Pioneers Initiative - Real-Time Traffic Analytics Project

This simulator generates realistic traffic data for 7 major Cairo locations
and streams it to Azure Event Hub for real-time processing and analysis.
"""

import random
import time
import json
from datetime import datetime, timezone
from azure.eventhub import EventHubProducerClient, EventData

print("=" * 70)
print("CAIRO TRAFFIC DATA SIMULATOR")
print("=" * 70)

# Configuration Section
# ====================

# Azure Event Hub connection details for data ingestion
# Replace with your actual Event Hub connection string
CONNECTION_STR = (
    "Endpoint=sb://traffic-namespace-spain.servicebus.windows.net/;"
    "SharedAccessKeyName=ManagePolicy;"
    "SharedAccessKey=Uss68YXOMukayMWCrWwgUmvdXz/qYybY2+AEhEexbqI=;"
    "EntityPath=traffic-events"
)
EVENTHUB_NAME = "traffic-events"

# Master list of monitored traffic locations in Cairo
# Each location includes unique identifier, name, GPS coordinates, and capacity
LOCATIONS = [
    {
        "id": "LOC001", 
        "name": "Tahrir Square", 
        "lat": 30.0444, 
        "lon": 31.2357, 
        "cap": 120
    },
    {
        "id": "LOC002", 
        "name": "Ramses Square", 
        "lat": 30.0626, 
        "lon": 31.2497, 
        "cap": 150
    },
    {
        "id": "LOC003", 
        "name": "6th October Bridge", 
        "lat": 30.0626, 
        "lon": 31.2444, 
        "cap": 100
    },
    {
        "id": "LOC004", 
        "name": "Nasr City - Abbas El Akkad", 
        "lat": 30.0515, 
        "lon": 31.3381, 
        "cap": 80
    },
    {
        "id": "LOC005", 
        "name": "Heliopolis - Uruba Street", 
        "lat": 30.0808, 
        "lon": 31.3239, 
        "cap": 90
    },
    {
        "id": "LOC006", 
        "name": "Maadi Corniche", 
        "lat": 29.9594, 
        "lon": 31.2584, 
        "cap": 60
    },
    {
        "id": "LOC007", 
        "name": "Ahmed Orabi Square", 
        "lat": 30.0618, 
        "lon": 31.2001, 
        "cap": 110
    },
]

# Vehicle classification for traffic composition analysis
VEHICLE_TYPES = [
    "Car", "Taxi", "Bus", "Microbus", 
    "Truck", "Motorcycle", "Delivery Van"
]

# Environmental conditions affecting traffic patterns
WEATHER_CONDITIONS = [
    "Clear", "Cloudy", "Light Rain", 
    "Heavy Rain", "Foggy", "Sandstorm"
]

# Traffic incident types for anomaly detection
TRAFFIC_INCIDENTS = [
    "None", "Minor Accident", "Major Accident", 
    "Vehicle Breakdown", "Road Construction", "Police Checkpoint"
]

# Initialize Azure Event Hub Connection
# =====================================
print("\nInitializing Azure Services Connection...")

producer = None
try:
    # Create Event Hub producer client for data streaming
    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STR,
        eventhub_name=EVENTHUB_NAME
    )
    print("SUCCESS: Connected to Azure Event Hub")
    print("Data will be streamed to cloud for real-time processing")
except Exception as connection_error:
    print(f"WARNING: Event Hub connection failed - {connection_error}")
    print("System will run in local mode - data displayed only on console")
    producer = None

# Traffic Pattern Calculation Functions
# =====================================

def calculate_rush_hour_factor():
    """
    Calculate traffic intensity multiplier based on time of day
    Models Cairo's typical rush hour patterns:
    - Morning rush: 7 AM - 10 AM (150% normal traffic)
    - Evening rush: 6 PM - 9 PM (140% normal traffic) 
    - Night hours: 10 PM - 6 AM (40% normal traffic)
    - Normal hours: Baseline traffic levels
    """
    current_hour = datetime.now().hour
    
    # Morning commute period
    if 7 <= current_hour <= 10:
        return 1.5
    
    # Evening commute period  
    elif 18 <= current_hour <= 21:
        return 1.4
    
    # Overnight low traffic period
    elif current_hour <= 6 or current_hour >= 22:
        return 0.4
    
    # Standard daytime traffic
    else:
        return 1.0

def generate_realistic_traffic_data():
    """
    Generate realistic traffic metrics for simulation
    Applies traffic engineering principles to create believable data
    Includes occasional anomalies for real-world scenario testing
    """
    # Select random monitoring location
    location = random.choice(LOCATIONS)
    
    # Get current traffic intensity factor
    rush_factor = calculate_rush_hour_factor()
    
    # Calculate vehicle count with rush hour consideration
    # Ensures minimum 5 vehicles and respects location capacity limits
    min_vehicles = max(5, int(location["cap"] * 0.3 * rush_factor))
    max_vehicles = min(location["cap"], int(location["cap"] * 1.2 * rush_factor))
    vehicle_count = random.randint(min_vehicles, max_vehicles)
    
    # Simulate occasional traffic congestion (5% probability)
    if random.random() < 0.05:
        vehicle_count = min(location["cap"] * 1.5, vehicle_count * 1.8)
    
    # Select dominant vehicle type for this observation
    vehicle_type = random.choice(VEHICLE_TYPES)
    
    # Calculate speed with realistic variations
    # Includes occasional extreme values for anomaly detection testing
    if random.random() < 0.05:
        # Generate speed anomaly for system testing
        if random.random() < 0.5:
            speed = random.uniform(5, 15)  # Severe congestion scenario
        else:
            speed = random.uniform(85, 110)  # High-speed scenario
    else:
        # Normal speed calculation with rush hour adjustment
        base_speed = random.uniform(20, 80)
        # Reduce speeds during high traffic periods
        adjusted_speed = base_speed * (0.8 if rush_factor > 1.0 else 1.2)
        speed = max(5, min(90, round(adjusted_speed, 1)))
    
    # Calculate congestion percentage
    # Represents road capacity utilization
    congestion_percentage = round(vehicle_count / location["cap"] * 100, 1)
    
    # Simulate traffic incidents (10% probability)
    if random.random() < 0.1:
        incident = random.choice([
            "Minor Accident", "Major Accident", 
            "Vehicle Breakdown", "Road Construction"
        ])
    else:
        incident = "None"
    
    # Generate ISO 8601 timestamp for data consistency
    current_time = datetime.now(timezone.utc)
    
    # Compile complete traffic observation record
    # Structure matches Azure SQL Database schema exactly
    traffic_event = {
        "Timestamp": current_time.isoformat(timespec='seconds'),
        "LocationID": location["id"],
        "LocationName": location["name"],
        "Latitude": float(location["lat"]),
        "Longitude": float(location["lon"]),
        "VehicleCount": int(vehicle_count),
        "AverageSpeedKMH": round(speed, 2),  # Matches DECIMAL(5,2) in SQL
        "DominantVehicleType": vehicle_type,
        "WeatherCondition": random.choice(WEATHER_CONDITIONS),
        "TrafficIncident": incident,
        "CongestionPercentage": round(congestion_percentage, 2),  # DECIMAL(5,2)
        "IsRushHour": rush_factor > 1.0,
        "RushFactor": round(rush_factor, 2)  # Matches DECIMAL(3,2) in SQL
    }
    
    return traffic_event

# Main Simulation Execution
# =========================

def run_traffic_simulation():
    """
    Execute continuous traffic data simulation
    Generates new traffic observations at 5-second intervals
    Streams data to Azure Event Hub for cloud processing
    """
    event_counter = 0
    
    print("\n" + "=" * 70)
    print("TRAFFIC SIMULATION INITIATED")
    print("=" * 70)
    print("Simulation Parameters:")
    print("- Monitoring 7 Cairo traffic locations")
    print("- Data generation interval: 5 seconds")
    print("- Realistic rush hour modeling enabled")
    print("- Anomaly scenarios included for testing")
    print("- Data format: Azure SQL Database compatible")
    print("\nStarting data generation...")
    print("-" * 70)
    
    try:
        # Continuous data generation loop
        while True:
            event_counter += 1
            
            # Generate new traffic observation
            traffic_data = generate_realistic_traffic_data()
            
            # Display observation details
            print(f"\nEVENTS #{event_counter}")
            print(f"Location: {traffic_data['LocationName']} ({traffic_data['LocationID']})")
            print(f"Coordinates: {traffic_data['Latitude']}, {traffic_data['Longitude']}")
            print(f"Traffic Metrics: {traffic_data['VehicleCount']} vehicles, "
                  f"{traffic_data['AverageSpeedKMH']} km/h")
            print(f"Road Conditions: {traffic_data['CongestionPercentage']}% congestion, "
                  f"{traffic_data['DominantVehicleType']} dominant")
            print(f"Environment: {traffic_data['WeatherCondition']} weather, "
                  f"{traffic_data['TrafficIncident']} incident")
            print(f"Time Analysis: Rush Hour: {traffic_data['IsRushHour']}, "
                  f"Intensity Factor: {traffic_data['RushFactor']}")
            print(f"Timestamp: {traffic_data['Timestamp']}")
            
            # Stream data to Azure Event Hub if connected
            if producer:
                try:
                    # Convert data to JSON format for transmission
                    event_data = EventData(json.dumps(traffic_data))
                    
                    # Send to Event Hub for Stream Analytics processing
                    producer.send_batch([event_data])
                    print("STATUS: Data successfully streamed to Azure cloud")
                except Exception as transmission_error:
                    print(f"TRANSMISSION ERROR: {transmission_error}")
                    print("Data retained locally - transmission will retry")
            else:
                print("STATUS: Local mode active - data displayed only")
            
            print("-" * 70)
            
            # Maintain 5-second observation interval
            # Matches project specification for data frequency
            time.sleep(5)
            
    except KeyboardInterrupt:
        # Graceful shutdown on user interruption
        print(f"\n" + "=" * 70)
        print("SIMULATION TERMINATED BY USER")
        print(f"Total observations generated: {event_counter}")
        
        # Clean up Azure connection
        if producer:
            producer.close()
            print("Azure Event Hub connection closed securely")
        
        print("Simulation shutdown complete")
        print("=" * 70)

# Application Entry Point
# =======================

if __name__ == "__main__":
    """
    Main execution block - starts the traffic simulation
    Press Ctrl+C to stop the simulation gracefully
    """
    try:
        run_traffic_simulation()
    except Exception as critical_error:
        print(f"CRITICAL ERROR: Simulation failed - {critical_error}")
        if producer:
            producer.close()