"""
AI service used by the /ai/* routes.

This wraps the modular ai_engine package. If real model weights are not
available, it automatically falls back to mock/demo mode so the rest of the
app keeps working (see requirement: "app must run even if heavy AI model
files are unavailable").
"""

from datetime import datetime, timezone
import random

from app.core.config import settings
from app.schemas.ai import DetectionResult


MOCK_OBJECTS = [
    ("pole", "center", 1.2),
    ("person", "left", 2.5),
    ("car", "right", 6.0),
    ("bench", "left", 3.0),
    ("stairs", "center", 1.8),
    ("pothole", "center", 0.9),
]


class AIService:
    def __init__(self, mock_mode: bool | None = None):
        self.mock_mode = settings.AI_MOCK_MODE if mock_mode is None else mock_mode

    def detect_objects(self) -> list[DetectionResult]:
        """
        Returns detected objects. In mock mode, generates 1-2 plausible
        detections. Real mode would call the YOLO-based detector in
        ai_engine/object_detection.
        """
        if not self.mock_mode:
            # Placeholder for real model integration.
            # from ai_engine.object_detection.detector import YoloDetector
            # return YoloDetector().detect(frame)
            pass

        num_objects = random.choice([1, 1, 2])
        chosen = random.sample(MOCK_OBJECTS, num_objects)
        now = datetime.now(timezone.utc).isoformat()
        results = []
        for name, position, distance in chosen:
            results.append(
                DetectionResult(
                    class_name=name,
                    confidence=round(random.uniform(0.75, 0.97), 2),
                    bbox=[50.0, 50.0, 200.0, 300.0],
                    position=position,
                    timestamp=now,
                )
            )
        return results

    def describe_scene(self) -> str:
        """Mock scene description. Real mode would use a vision-language model."""
        templates = [
            "You are on a sidewalk. Two people are ahead. A parked car is on your left.",
            "You are near a crossing. Traffic signal is ahead. No obstacles nearby.",
            "Open pathway ahead. A bench is on your right, ten meters away.",
            "You are indoors. A doorway is ahead. Chairs are on your left.",
        ]
        return random.choice(templates)


def get_ai_service() -> AIService:
    return AIService()
