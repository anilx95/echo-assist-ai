"""
Import all model modules here so SQLAlchemy's mapper registry can resolve
string-based relationship() references (e.g. "EmergencyContact") regardless
of which module is imported first.
"""

from app.models import (  # noqa: F401
    user,
    contact,
    device,
    sensor_reading,
    detection_event,
    risk_event,
    emergency_event,
    navigation_route,
    saved_location,
    user_settings,
    user_profile,
    notification,
    system_log,
    refresh_session,
    account_token,
)
