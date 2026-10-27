class DecisionEngineService:

    def decide(
        self,
        object_type: str,
        distance_cm: float,
        direction: str,
        risk_level: str,
        confidence: float,
    ) -> dict:

        object_type = object_type.lower()
        direction = direction.lower()
        risk_level = risk_level.upper()

        # Rule 1: Stairs
        if object_type == "stairs":
            return {
                "action": "STOP",
                "voice_message": "Warning. Stairs ahead. Stop.",
                "vibration": "STRONG",
                "priority": 1,
            }

        # Rule 2: Pothole
        if object_type == "pothole":
            return {
                "action": "STOP_AND_AVOID",
                "voice_message": "Warning. Pothole ahead. Stop and change direction.",
                "vibration": "STRONG",
                "priority": 1,
            }

        # Rule 3: Critical risk
        if risk_level == "CRITICAL":
            return {
                "action": "STOP",
                "voice_message": (
                    f"Danger. {object_type} very close ahead. Stop immediately."
                ),
                "vibration": "STRONG",
                "priority": 1,
            }

        # Rule 4: High risk on left
        if risk_level == "HIGH" and direction == "left":
            return {
                "action": "MOVE_RIGHT",
                "voice_message": (
                    f"{object_type} on the left. Move right."
                ),
                "vibration": "MEDIUM",
                "priority": 2,
            }

        # Rule 5: High risk on right
        if risk_level == "HIGH" and direction == "right":
            return {
                "action": "MOVE_LEFT",
                "voice_message": (
                    f"{object_type} on the right. Move left."
                ),
                "vibration": "MEDIUM",
                "priority": 2,
            }

        # Rule 6: High risk in center
        if risk_level == "HIGH" and direction == "center":
            return {
                "action": "CAUTION",
                "voice_message": (
                    f"Warning. {object_type} ahead at "
                    f"{round(distance_cm / 100, 1)} meters."
                ),
                "vibration": "STRONG",
                "priority": 2,
            }

        # Rule 7: Medium risk
        if risk_level == "MEDIUM":
            return {
                "action": "SLOW_DOWN",
                "voice_message": (
                    f"Caution. {object_type} detected ahead."
                ),
                "vibration": "LIGHT",
                "priority": 3,
            }

        # Rule 8: Low risk
        return {
            "action": "CONTINUE",
            "voice_message": "Path is clear. Continue forward.",
            "vibration": "NONE",
            "priority": 4,
        }


decision_engine_service = DecisionEngineService()