from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    class_name: str
    confidence: float = Field(ge=0, le=1)
    bbox: list[float] = Field(description="[x1, y1, x2, y2]")
    position: str = Field(description="left|center|right")
    timestamp: str


class DetectRequest(BaseModel):
    image_base64: str | None = None
    use_mock: bool = True


class DetectResponse(BaseModel):
    detections: list[DetectionResult]
    mock_mode: bool


class RiskRequest(BaseModel):
    object_name: str
    fused_distance_m: float
    direction: str = "center"
    is_approaching: bool = False
    confidence: float = 0.9


class RiskResponse(BaseModel):
    object_name: str
    fused_distance_m: float
    direction: str
    risk_level: str  # SAFE|WARNING|DANGER
    message: str
    priority: int
    vibration_pattern: str


class SceneDescriptionRequest(BaseModel):
    use_mock: bool = True


class SceneDescriptionResponse(BaseModel):
    description: str
    mock_mode: bool
