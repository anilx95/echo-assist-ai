"""
Phase 1 smoke tests: app boots, DB initializes, auth + core routes work.
More targeted tests (sensor fusion, risk engine, etc.) land in later phases
per the master prompt's development order.
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.database import engine


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_local_development_cors_allows_dynamic_local_port(client):
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://127.0.0.1:4321",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:4321"


def test_register_and_login(client):
    register_payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "testpass123",
    }
    r = client.post("/auth/register", json=register_payload)
    assert r.status_code == 201
    assert "access_token" in r.json()
    r = client.post(
        "/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_is_case_insensitive_for_email(client):
    payload = {
        "full_name": "Case User",
        "email": "Case.Sensitive@Example.com",
        "password": "testpass123",
    }
    assert client.post("/auth/register", json=payload).status_code == 201
    response = client.post(
        "/auth/login",
        json={"email": "case.sensitive@example.com", "password": payload["password"]},
    )
    assert response.status_code == 200

def test_register_duplicate_email_rejected(client):
    payload = {"full_name": "A", "email": "dup@example.com", "password": "testpass123"}
    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 409


def test_protected_route_requires_token(client):
    r = client.get("/user/profile")
    assert r.status_code == 401


def test_sensor_data_ingestion_and_latest(client):
    register = client.post(
        "/auth/register",
        json={"full_name": "Sensor User", "email": "sensor@example.com", "password": "testpass123"},
    )
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    device = client.post("/devices", json={"device_id": "ECHO_CANE_TEST", "is_simulator": True}, headers=headers)
    assert device.status_code == 201

    packet = {
        "device_id": "ECHO_CANE_TEST",
        "ultrasonic_cm": 115,
        "tof_mm": 1200,
        "sos_pressed": False,
        "battery_percent": 90,
        "timestamp": 1710000000,
    }
    r = client.post("/sensors/data", json=packet, headers=headers)
    assert r.status_code == 201

    r = client.get("/sensors/latest", headers=headers)
    assert r.status_code == 200
    assert r.json()["ultrasonic_cm"] == 115

    history = client.get("/sensors/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_ai_risk_danger_classification(client):
    register = client.post(
        "/auth/register",
        json={"full_name": "Risk User", "email": "risk@example.com", "password": "testpass123"},
    )
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/ai/risk",
        json={"object_name": "pole", "fused_distance_m": 0.5, "direction": "center"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["risk_level"] == "DANGER"
