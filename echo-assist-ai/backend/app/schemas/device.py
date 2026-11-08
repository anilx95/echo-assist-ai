from datetime import datetime

from pydantic import BaseModel, Field


class DeviceCreateRequest(BaseModel):
    device_id: str = Field(min_length=3, max_length=64)
    device_name: str = Field(default="ECHO-CANE", min_length=1, max_length=120)
    firmware_version: str | None = Field(default=None, max_length=20)
    is_simulator: bool = False


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_name: str
    firmware_version: str | None
    connection_status: str
    battery_percent: float | None
    sensor_health: str
    is_simulator: bool
    last_connected_at: datetime | None

    model_config = {"from_attributes": True}


class PreferenceResponse(BaseModel):
    language: str
    voice_alerts_enabled: bool
    vibration_alerts_enabled: bool
    high_contrast_mode: bool
    large_text_mode: bool
    fall_detection_enabled: bool
    fall_detection_countdown_seconds: int

    model_config = {"from_attributes": True}


class PreferenceUpdateRequest(BaseModel):
    language: str | None = Field(default=None, max_length=10)
    voice_alerts_enabled: bool | None = None
    vibration_alerts_enabled: bool | None = None
    high_contrast_mode: bool | None = None
    large_text_mode: bool | None = None
    fall_detection_enabled: bool | None = None
    fall_detection_countdown_seconds: int | None = Field(default=None, ge=5, le=120)
