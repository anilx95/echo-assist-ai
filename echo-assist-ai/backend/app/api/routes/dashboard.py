from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device import Device
from app.models.emergency_event import EmergencyEvent
from app.models.risk_event import RiskEvent
from app.models.sensor_reading import SensorReading
from app.models.user import User
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    devices = db.query(Device).filter(Device.user_id == current_user.id).order_by(Device.last_connected_at.desc()).all()
    device_ids = [device.id for device in devices]
    latest_reading = (
        db.query(SensorReading).filter(SensorReading.device_id.in_(device_ids))
        .order_by(SensorReading.received_at.desc()).first()
        if device_ids else None
    )
    latest_risk = db.query(RiskEvent).filter(RiskEvent.user_id == current_user.id).order_by(RiskEvent.created_at.desc()).first()
    active_sos = db.query(EmergencyEvent).filter(
        EmergencyEvent.user_id == current_user.id,
        EmergencyEvent.status.in_(["ACTIVE", "PENDING_CONFIRMATION"]),
    ).order_by(EmergencyEvent.created_at.desc()).first()
    return {
        "device_count": len(devices),
        "connected_devices": sum(1 for device in devices if device.connection_status == "connected"),
        "latest_sensor_reading": {
            "battery_percent": latest_reading.battery_percent,
            "received_at": latest_reading.received_at,
        } if latest_reading else None,
        "latest_risk": {
            "risk_level": latest_risk.risk_level,
            "message": latest_risk.message,
            "created_at": latest_risk.created_at,
        } if latest_risk else None,
        "active_sos": {"id": active_sos.id, "status": active_sos.status, "created_at": active_sos.created_at} if active_sos else None,
        "devices": [DeviceResponse.model_validate(device).model_dump() for device in devices],
    }


from app.schemas.device import DeviceResponse  # imported after route dependencies for readability
