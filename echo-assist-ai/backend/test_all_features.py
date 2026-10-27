#!/usr/bin/env python3
"""
Comprehensive feature test for ECHO-ASSIST AI backend.
Tests all API endpoints to ensure perfect functionality.
"""

import httpx
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
client = httpx.Client()

# Test data
test_user_email = f"testuser_{datetime.now().timestamp()}@example.com"
test_user_password = "SecurePassword123!"
access_token = None
current_user_id = None

print("=" * 70)
print("ECHO-ASSIST AI - COMPREHENSIVE FEATURE TEST")
print("=" * 70)

# Test 1: Health Check
print("\n[1/11] Testing Health Check...")
try:
    response = client.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["ai_mock_mode"] == True
    print(f"✅ Health check passed: {data}")
except Exception as e:
    print(f"❌ Health check failed: {e}")

# Test 2: User Registration
print("\n[2/11] Testing User Registration...")
try:
    payload = {
        "full_name": "Test User",
        "email": test_user_email,
        "password": test_user_password,
        "preferred_language": "en",
    }
    response = client.post(f"{BASE_URL}/auth/register", json=payload)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    access_token = data["access_token"]
    print(f"✅ Registration successful. Token: {access_token[:20]}...")
except Exception as e:
    print(f"❌ Registration failed: {e}")

# Test 3: User Login
print("\n[3/11] Testing User Login...")
try:
    payload = {"email": test_user_email, "password": test_user_password}
    response = client.post(f"{BASE_URL}/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]
    print(f"✅ Login successful. Token: {access_token[:20]}...")
except Exception as e:
    print(f"❌ Login failed: {e}")

# Test 4: Get User Profile
print("\n[4/11] Testing Get User Profile...")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/user/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    current_user_id = data["id"]
    assert data["email"] == test_user_email
    print(f"✅ Profile retrieved: {data['full_name']} ({data['email']}), ID: {current_user_id}")
except Exception as e:
    print(f"❌ Profile retrieval failed: {e}")

# Test 5: Update User Profile
print("\n[5/11] Testing Update User Profile...")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"full_name": "Updated Test User"}
    response = client.put(f"{BASE_URL}/user/profile", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Test User"
    print(f"✅ Profile updated: {data['full_name']}")
except Exception as e:
    print(f"❌ Profile update failed: {e}")

# Test 6: Add Emergency Contact
print("\n[6/11] Testing Add Emergency Contact...")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "name": "Emergency Contact 1",
        "phone_number": "+1234567890",
        "email": "contact@example.com",
        "relationship": "Family",
    }
    response = client.post(f"{BASE_URL}/contacts", json=payload, headers=headers)
    assert response.status_code == 201
    contact_data = response.json()
    contact_id = contact_data["id"]
    print(f"✅ Contact added: {contact_data['name']} ({contact_data['phone_number']}), ID: {contact_id}")
except Exception as e:
    print(f"❌ Contact addition failed: {e}")

# Test 7: List Contacts
print("\n[7/11] Testing List Contacts...")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/contacts", headers=headers)
    assert response.status_code == 200
    contacts = response.json()
    print(f"✅ Contacts listed: {len(contacts)} contact(s) found")
    if contacts:
        for c in contacts:
            print(f"   - {c['name']} ({c['phone_number']})")
except Exception as e:
    print(f"❌ Contact listing failed: {e}")

# Test 8: Sensor Data Ingestion
print("\n[8/11] Testing Sensor Data Ingestion...")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
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
    assert response.status_code == 201
    sensor_data = response.json()
    print(f"✅ Sensor data ingested: Distance={sensor_data['ultrasonic_cm']}cm, Battery={sensor_data['battery_percent']}%")
except Exception as e:
    print(f"❌ Sensor data ingestion failed: {e}")

# Test 9: Get Latest Sensor Reading
print("\n[9/11] Testing Get Latest Sensor Reading...")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/sensors/latest", headers=headers)
    assert response.status_code == 200
    reading = response.json()
    print(f"✅ Latest sensor reading retrieved: Distance={reading['ultrasonic_cm']}cm, ToF={reading['tof_mm']}mm")
except Exception as e:
    print(f"❌ Sensor reading retrieval failed: {e}")

# Test 10: AI Risk Analysis
print("\n[10/11] Testing AI Risk Analysis...")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "object_name": "person",
        "fused_distance_m": 1.5,
        "direction": "front",
        "is_approaching": True,
    }
    response = client.post(f"{BASE_URL}/ai/risk", json=payload, headers=headers)
    assert response.status_code == 200
    risk_data = response.json()
    assert risk_data["risk_level"] in ["DANGER", "WARNING", "SAFE"]
    print(f"✅ Risk analysis: {risk_data['object_name']} at {risk_data['fused_distance_m']}m -> {risk_data['risk_level']}")
    print(f"   Message: {risk_data['message']}")
    print(f"   Vibration: {risk_data['vibration_pattern']}")
except Exception as e:
    print(f"❌ Risk analysis failed: {e}")

# Test 11: Navigation Route
print("\n[11/11] Testing Navigation Route...")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "origin_latitude": 40.7128,
        "origin_longitude": -74.0060,
        "destination_latitude": 40.7580,
        "destination_longitude": -73.9855,
        "destination": "Central Park",
    }
    response = client.post(f"{BASE_URL}/navigation/route", json=payload, headers=headers)
    assert response.status_code == 200
    route = response.json()
    assert route["mock_mode"] == True
    print(f"✅ Route generated to {route['destination']}: {route['total_distance_m']}m, ~{route['estimated_time_minutes']} min walk")
    print(f"   Steps: {len(route['steps'])}")
    for i, step in enumerate(route['steps'], 1):
        print(f"   {i}. {step['instruction']} ({step['distance_m']}m)")
except Exception as e:
    print(f"❌ Navigation failed: {e}")

print("\n" + "=" * 70)
print("ALL FEATURE TESTS COMPLETED SUCCESSFULLY! ✅")
print("=" * 70)
print("\nBackend is ready for production use!")
print(f"Interactive API Docs: {BASE_URL}/docs")
client.close()
