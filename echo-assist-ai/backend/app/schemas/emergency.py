from datetime import datetime

from pydantic import BaseModel, Field


class EmergencyTriggerRequest(BaseModel):
    event_type: str = Field(
        description="FALL_DETECTED|MANUAL_SOS|VOICE_SOS"
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )


class EmergencyCancelRequest(BaseModel):
    emergency_id: int


class EmergencyEventResponse(BaseModel):
    id: int
    event_type: str

    latitude: float | None = None
    longitude: float | None = None

    status: str
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = {
        "from_attributes": True
    }


class FallDetectionResponse(BaseModel):
    sensor_reading_id: int

    fall_detected: bool
    emergency_detected: bool

    event_type: str
    confidence: float

    acceleration_magnitude: float
    gyro_magnitude: float

    severity: str
    reason: str

    emergency_created: bool = False
    emergency_id: int | None = None