from pydantic import BaseModel, Field
from datetime import datetime


class SensorPacket(BaseModel):
    """Matches the ESP32 BLE packet format defined in docs/ble_protocol.md."""

    device_id: str = Field(min_length=1, max_length=64)
    ultrasonic_cm: float | None = None
    tof_mm: float | None = None
    accel_x: float | None = None
    accel_y: float | None = None
    accel_z: float | None = None
    gyro_x: float | None = None
    gyro_y: float | None = None
    gyro_z: float | None = None
    sos_pressed: bool = False
    battery_percent: float | None = Field(default=None, ge=0, le=100)
    timestamp: int | str | None = None  # Accept both Unix timestamp and ISO string


class SensorReadingResponse(BaseModel):
    id: int
    ultrasonic_cm: float | None
    tof_mm: float | None
    accel_x: float | None
    accel_y: float | None
    accel_z: float | None
    gyro_x: float | None
    gyro_y: float | None
    gyro_z: float | None
    sos_pressed: bool
    battery_percent: float | None
    device_timestamp: int | None

    model_config = {"from_attributes": True}
