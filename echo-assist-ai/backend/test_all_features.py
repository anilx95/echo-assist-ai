#!/usr/bin/env python3
"""
Comprehensive feature test for ECHO-ASSIST AI backend.
Tests all API endpoints to ensure perfect functionality against a live running server.
"""

import sys
from datetime import datetime
import httpx


def run_tests():
    base_url = "http://127.0.0.1:8000"
    client = httpx.Client()
    failed = 0

    test_user_email = f"testuser_{datetime.now().timestamp()}@example.com"
    test_user_password = "SecurePassword123!"
    access_token = None

    print("=" * 70)
    print("ECHO-ASSIST AI - COMPREHENSIVE FEATURE TEST")
    print("=" * 70)

    # Test 1: Health Check
    print("\n[1/11] Testing Health Check...")
    try:
        response = client.get(f"{base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"✅ Health check passed: {data}")
    except Exception as e:
        failed += 1
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
        response = client.post(f"{base_url}/auth/register", json=payload)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        access_token = data["access_token"]
        print(f"✅ Registration successful. Token: {access_token[:20]}...")
    except Exception as e:
        failed += 1
        print(f"❌ Registration failed: {e}")

    # Test 3: User Login
    print("\n[3/11] Testing User Login...")
    try:
        payload = {"email": test_user_email, "password": test_user_password}
        response = client.post(f"{base_url}/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        access_token = data["access_token"]
        print(f"✅ Login successful.")
    except Exception as e:
        failed += 1
        print(f"❌ Login failed: {e}")

    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}

    # Test 4: Get Profile
    print("\n[4/11] Testing Get User Profile...")
    try:
        response = client.get(f"{base_url}/user/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ User profile retrieved: {data['full_name']} ({data['email']})")
    except Exception as e:
        failed += 1
        print(f"❌ Profile retrieval failed: {e}")

    # Test 5: Update Profile
    print("\n[5/11] Testing Update User Profile...")
    try:
        payload = {
            "phone_number": "+1234567890",
            "address": "123 Accessibility Way",
        }
        response = client.put(f"{base_url}/user/profile", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Profile updated: Phone={data.get('phone_number')}, Address={data.get('address')}")
    except Exception as e:
        failed += 1
        print(f"❌ Profile update failed: {e}")

    # Test 6: Add Emergency Contact
    print("\n[6/11] Testing Add Emergency Contact...")
    try:
        payload = {
            "name": "Jane Caregiver",
            "relationship_type": "Caregiver",
            "phone_number": "+1987654321",
            "email": "jane@example.com",
        }
        response = client.post(f"{base_url}/contacts", json=payload, headers=headers)
        assert response.status_code == 201
        data = response.json()
        print(f"✅ Emergency contact added: {data['name']} ({data['relationship_type']})")
    except Exception as e:
        failed += 1
        print(f"❌ Contact addition failed: {e}")

    # Test 7: List Emergency Contacts
    print("\n[7/11] Testing List Contacts...")
    try:
        response = client.get(f"{base_url}/contacts", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Contacts retrieved: {len(data)} contact(s) found")
    except Exception as e:
        failed += 1
        print(f"❌ Contact listing failed: {e}")

    # Test 8: Ingest Sensor Data
    print("\n[8/11] Testing Sensor Data Ingestion...")
    try:
        device_payload = {"device_id": "TEST_CANE_001", "is_simulator": True}
        client.post(f"{base_url}/devices", json=device_payload, headers=headers)

        payload = {
            "device_id": "TEST_CANE_001",
            "ultrasonic_cm": 45.5,
            "tof_mm": 450.0,
            "accel_x": 0.1,
            "accel_y": 0.2,
            "accel_z": 9.8,
            "gyro_x": 0.01,
            "gyro_y": 0.02,
            "gyro_z": 0.01,
            "battery_percent": 88.0,
            "sos_pressed": False,
        }
        response = client.post(f"{base_url}/sensors/data", json=payload, headers=headers)
        assert response.status_code == 201
        data = response.json()
        print(f"✅ Sensor reading ingested: Fused Distance={data['fused_distance_cm']}cm, Status={data['fusion_status']}")
    except Exception as e:
        failed += 1
        print(f"❌ Sensor data ingestion failed: {e}")

    # Test 9: Get Latest Sensor Reading
    print("\n[9/11] Testing Get Latest Sensor Reading...")
    try:
        response = client.get(f"{base_url}/sensors/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Latest reading: Ultrasonic={data['ultrasonic_cm']}cm, Battery={data['battery_percent']}%")
    except Exception as e:
        failed += 1
        print(f"❌ Sensor reading retrieval failed: {e}")

    # Test 10: AI Risk Analysis
    print("\n[10/11] Testing AI Risk Analysis...")
    try:
        payload = {
            "object_name": "pole",
            "fused_distance_m": 1.2,
            "direction": "center",
        }
        response = client.post(f"{base_url}/ai/risk", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Risk predicted: Level={data['risk_level']}, Confidence={data['confidence']}")
    except Exception as e:
        failed += 1
        print(f"❌ Risk analysis failed: {e}")

    # Test 11: Navigation History / Route
    print("\n[11/11] Testing Navigation Endpoint...")
    try:
        response = client.get(f"{base_url}/navigation/history", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Navigation history endpoint functional ({len(data)} routes)")
    except Exception as e:
        failed += 1
        print(f"❌ Navigation failed: {e}")

    print("\n" + "=" * 70)
    if failed == 0:
        print("ALL FEATURE TESTS COMPLETED SUCCESSFULLY! ✅")
    else:
        print(f"FEATURE TESTS COMPLETED WITH {failed} FAILURE(S). ❌")
    print("=" * 70)
    client.close()
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
