from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class RouteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    origin_lat: float | None = Field(
        default=None,
        alias="origin_latitude",
    )

    origin_lng: float | None = Field(
        default=None,
        alias="origin_longitude",
    )

    destination_lat: float | None = Field(
        default=None,
        alias="destination_latitude",
    )

    destination_lng: float | None = Field(
        default=None,
        alias="destination_longitude",
    )

    destination: str


class RouteStep(BaseModel):
    step_number: int
    instruction: str
    distance_m: float
    direction: str
    voice_instruction: str


class RouteResponse(BaseModel):
    route_id: str
    destination: str
    total_distance_m: float
    estimated_time_minutes: float
    steps: list[RouteStep]
    current_step: int
    current_instruction: str
    navigation_status: str
    mock_mode: bool


class NavigationProgressRequest(BaseModel):
    route_id: str

    current_latitude: float = Field(
        ge=-90,
        le=90,
    )

    current_longitude: float = Field(
        ge=-180,
        le=180,
    )

class NavigationProgressResponse(BaseModel):
    route_id: str
    navigation_status: str

    current_step: int
    current_instruction: str

    remaining_distance_m: float

    off_route: bool
    rerouting_required: bool

    voice_instruction: str

    # Automatic rerouting information
    rerouted: bool = False

    previous_route_id: str | None = None

    total_distance_m: float | None = None

    estimated_time_minutes: float | None = None


class NavigationHistoryResponse(BaseModel):
    route_id: str
    destination: str
    total_distance_m: float
    estimated_time_minutes: float
    navigation_status: str
    mock_mode: bool
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
