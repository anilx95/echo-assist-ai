from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.services.account_token_service import (
    EMAIL_VERIFICATION,
    PASSWORD_RESET,
    issue_account_token,
)


def _account(client: TestClient, email: str = "phase3@example.com") -> tuple[dict, dict]:
    response = client.post("/auth/register", json={
        "full_name": "Phase Three User", "email": email, "password": "safe-password-123",
    })
    assert response.status_code == 201
    tokens = response.json()
    return tokens, {"Authorization": f"Bearer {tokens['access_token']}"}


def test_profile_devices_preferences_and_session_logout(client):
    tokens, headers = _account(client)
    profile = client.put("/user/profile", json={
        "phone_number": "+15551234567", "date_of_birth": "1990-01-02",
        "address": "1 Accessible Way", "medical_accessibility_preferences": "Voice alerts preferred",
    }, headers=headers)
    assert profile.status_code == 200
    assert profile.json()["address"] == "1 Accessible Way"

    device = client.post("/devices", json={"device_id": "TEST-CANE-001", "is_simulator": True}, headers=headers)
    assert device.status_code == 201
    assert device.json()["is_simulator"] is True
    assert client.get("/devices", headers=headers).json()[0]["device_id"] == "TEST-CANE-001"

    preferences = client.put("/devices/preferences/me", json={"large_text_mode": False}, headers=headers)
    assert preferences.status_code == 200
    assert preferences.json()["large_text_mode"] is False

    refreshed = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert client.post("/auth/logout", json={"refresh_token": refreshed.json()["refresh_token"]}).status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": refreshed.json()["refresh_token"]}).status_code == 401


def test_sos_dashboard_and_notification_delivery_state(client):
    _, headers = _account(client, "sos@example.com")
    contact = client.post("/contacts", json={
        "name": "Caregiver", "relationship_type": "Family", "phone_number": "+15550000001",
        "email": "caregiver@example.com",
    }, headers=headers)
    assert contact.status_code == 201
    alert = client.post("/emergency/trigger", json={"event_type": "MANUAL_SOS"}, headers=headers)
    assert alert.status_code == 201
    dashboard = client.get("/dashboard/overview", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["active_sos"]["id"] == alert.json()["id"]
    notifications = client.get("/notifications", headers=headers)
    assert notifications.status_code == 200
    assert notifications.json()
    assert {item["status"] for item in notifications.json()} == {"not_delivered"}


def test_web_dashboard_navigation_history_and_physical_sos(client):
    _, headers = _account(client, "hardware@example.com")
    assert client.get("/").status_code == 200
    assert client.get("/navigation/history", headers=headers).json() == []
    route = client.post("/navigation/route", json={"destination": "Hospital"}, headers=headers)
    assert route.status_code == 503

    device = client.post(
        "/devices",
        json={"device_id": "TEST-CANE-SOS", "is_simulator": True},
        headers=headers,
    )
    assert device.status_code == 201
    reading = client.post(
        "/sensors/data",
        json={"device_id": "TEST-CANE-SOS", "sos_pressed": True, "battery_percent": 80},
        headers=headers,
    )
    assert reading.status_code == 201
    emergency_history = client.get("/emergency/history", headers=headers)
    assert emergency_history.status_code == 200
    assert emergency_history.json()[0]["status"] == "ACTIVE"
    assert emergency_history.json()[0]["event_type"] == "MANUAL_SOS"


def test_password_reset_and_email_verification_tokens_are_one_time(client):
    tokens, headers = _account(client, "recover@example.com")
    assert client.post("/auth/forgot-password", json={"email": "recover@example.com"}).status_code == 202
    assert client.post("/auth/forgot-password", json={"email": "unknown@example.com"}).status_code == 202
    assert client.post("/auth/request-email-verification", headers=headers, json={}).status_code == 202

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "recover@example.com").one()
        reset_token = issue_account_token(
            db, user_id=user.id, purpose=PASSWORD_RESET, expires_in_minutes=30
        )
        verify_token = issue_account_token(
            db, user_id=user.id, purpose=EMAIL_VERIFICATION, expires_in_minutes=30
        )
        db.commit()

    reset = client.post("/auth/reset-password", json={
        "token": reset_token, "new_password": "new-safe-password-123",
    })
    assert reset.status_code == 204
    assert client.post("/auth/reset-password", json={
        "token": reset_token, "new_password": "another-safe-password-123",
    }).status_code == 400
    assert client.post("/auth/login", json={
        "email": "recover@example.com", "password": "safe-password-123",
    }).status_code == 401
    assert client.post("/auth/login", json={
        "email": "recover@example.com", "password": "new-safe-password-123",
    }).status_code == 200

    verified = client.post("/auth/verify-email", json={"token": verify_token})
    assert verified.status_code == 200
    assert client.post("/auth/verify-email", json={"token": verify_token}).status_code == 400
