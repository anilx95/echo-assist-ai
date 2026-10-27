from pydantic import BaseModel, Field

from app.schemas.navigation import RouteStep


class VoiceCommandRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=500,
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

class VoiceCommandResponse(BaseModel):
    recognized_text: str
    intent: str
    destination: str | None = None
    confidence: float
    response: str


class VoiceNavigationRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=500,
    )

    origin_latitude: float | None = None
    origin_longitude: float | None = None
    destination_latitude: float | None = None
    destination_longitude: float | None = None


class VoiceNavigationResponse(BaseModel):
    recognized_text: str
    intent: str
    destination: str | None = None
    command_response: str
    navigation_started: bool

    route_id: str | None = None
    total_distance_m: float | None = None
    estimated_time_minutes: float | None = None
    navigation_status: str | None = None

    current_instruction: str | None = None
    voice_instruction: str | None = None

    steps: list[RouteStep] = []


class AudioCommandResponse(BaseModel):
    transcription: str
    detected_language: str
    language_probability: float

    intent: str
    destination: str | None = None
    command_response: str


class AudioNavigationResponse(BaseModel):
    transcription: str
    detected_language: str
    language_probability: float

    intent: str
    destination: str | None = None
    command_response: str

    navigation_started: bool

    route_id: str | None = None
    total_distance_m: float | None = None
    estimated_time_minutes: float | None = None
    navigation_status: str | None = None

    current_instruction: str | None = None
    voice_instruction: str | None = None

    steps: list[RouteStep] = []