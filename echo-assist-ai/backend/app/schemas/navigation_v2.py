from pydantic import BaseModel, Field, ConfigDict


class RouteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    origin_lat: float | None = Field(default=None, alias="origin_latitude")
    origin_lng: float | None = Field(default=None, alias="origin_longitude")
    destination_lat: float | None = Field(default=None, alias="destination_latitude")
    destination_lng: float | None = Field(default=None, alias="destination_longitude")
    destination: str


class RouteStep(BaseModel):
    instruction: str
    distance_m: float


class RouteResponse(BaseModel):
    destination: str
    total_distance_m: float
    estimated_time_minutes: float
    steps: list[RouteStep]
    mock_mode: bool
