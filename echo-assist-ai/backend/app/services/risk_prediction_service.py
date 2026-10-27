from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = (
    PROJECT_ROOT
    / "ai_engine"
    / "risk_prediction"
    / "models"
    / "risk_model.joblib"
)


class RiskPredictionService:

    RISK_LABELS = {
        0: "LOW",
        1: "MEDIUM",
        2: "HIGH",
        3: "CRITICAL",
    }

    OBJECT_RISK = {
        "person": 2,
        "pole": 2,
        "car": 5,
        "dog": 3,
        "bike": 4,
        "bicycle": 4,
        "chair": 2,
        "bench": 2,
        "door": 1,
        "tree": 3,
        "bus": 5,
        "stairs": 5,
        "pothole": 5,
        "traffic_light": 1,
        "zebra_crossing": 1,
    }

    def __init__(self):

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Risk model not found: {MODEL_PATH}"
            )

        self.model = joblib.load(MODEL_PATH)

        print(
            f"Risk Prediction Model loaded: {MODEL_PATH}"
        )


    def predict(
        self,
        object_type: str,
        distance_cm: float,
        speed: float = 0.0,
        direction: str = "center",
        surface_risk: int = 1,
        lighting_risk: int = 1,
    ):

        object_name = object_type.lower()

        object_risk = self.OBJECT_RISK.get(
            object_name,
            2
        )

        direction_value = (
            1 if direction.lower() == "center" else 0
        )

        features = pd.DataFrame(
            [{
                "distance_cm": distance_cm,
                "speed": speed,
                "direction": direction_value,
                "object_risk": object_risk,
                "surface_risk": surface_risk,
                "lighting_risk": lighting_risk,
            }]
        )

        prediction = int(
            self.model.predict(features)[0]
        )

        probabilities = self.model.predict_proba(
            features
        )[0]

        confidence = float(
            max(probabilities)
        )

        return {
            "object_type": object_type,
            "distance_cm": round(distance_cm, 2),
            "speed": speed,
            "direction": direction,
            "risk_class": prediction,
            "risk_level": self.RISK_LABELS[prediction],
            "confidence": round(confidence, 4),
        }


risk_prediction_service = RiskPredictionService()