from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device import Device
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.device import (
    DeviceCreateRequest,
    DeviceResponse,
    PreferenceResponse,
    PreferenceUpdateRequest,
)
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceResponse])
def list_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Device).filter(Device.user_id == current_user.id).order_by(Device.created_at.desc()).all()


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    payload: DeviceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if existing and existing.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device is already registered")
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device is already registered to your account")
    device = Device(user_id=current_user.id, **payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_device(device_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id, Device.user_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    db.delete(device)
    db.commit()
    return None


@router.get("/preferences/me", response_model=PreferenceResponse)
def get_preferences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    preferences = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not preferences:
        preferences = UserSettings(user_id=current_user.id, language=current_user.preferred_language)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return preferences


@router.put("/preferences/me", response_model=PreferenceResponse)
def update_preferences(
    payload: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not preferences:
        preferences = UserSettings(user_id=current_user.id, language=current_user.preferred_language)
        db.add(preferences)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(preferences, field, value)
        if field == "language":
            current_user.preferred_language = value
    db.commit()
    db.refresh(preferences)
    return preferences
