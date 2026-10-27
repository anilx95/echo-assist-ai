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