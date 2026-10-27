#!/usr/bin/env python3
"""
Detailed error checking for failing endpoints.
"""

import httpx
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
client = httpx.Client()

# First register and login
test_user_email = f"testuser_{datetime.now().timestamp()}@example.com"
test_user_password = "SecurePassword123!"

# Register
reg_payload = {
    "full_name": "Test User",
    "email": test_user_email,
    "password": test_user_password,
    "preferred_language": "en",
}
reg_response = client.post(f"{BASE_URL}/auth/register", json=reg_payload)
access_token = reg_response.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}

# Test Contact Addition with detailed error
print("Testing Contact Addition...")
try:
    payload = {
        "name": "Emergency Contact 1",
        "phone_number": "+1234567890",
        "email": "contact@example.com",
        "relationship": "Family",
    }
    response = client.post(f"{BASE_URL}/contacts", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"JSON: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'N/A'}")

# Test Sensor Data with detailed error
print("\n\nTesting Sensor Data Ingestion...")
try:
    payload = {
        "device_id": "esp32_001",
        "ultrasonic_cm": 150,
        "tof_mm": 1500,
        "accel_x": 0.1,
        "accel_y": 0.2,
        "accel_z": 9.8,
        "gyro_x": 0.05,
        "gyro_y": 0.1,
        "gyro_z": 0.02,
        "sos_pressed": False,
        "battery_percent": 85,
        "timestamp": datetime.now().isoformat(),
    }
    response = client.post(f"{BASE_URL}/sensors/data", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"JSON: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'N/A'}")

# Test Navigation with detailed error
print("\n\nTesting Navigation...")
try:
    payload = {
        "origin_latitude": 40.7128,
        "origin_longitude": -74.0060,
        "destination_latitude": 40.7580,
        "destination_longitude": -73.9855,
        "destination": "Central Park",
    }
    response = client.post(f"{BASE_URL}/navigation/route", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"JSON: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'N/A'}")

client.close()
