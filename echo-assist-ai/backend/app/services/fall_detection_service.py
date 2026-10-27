import math


class FallDetectionService:
    """
    Rule-based fall detection for MVP.

    Uses:
    - acceleration magnitude
    - gyroscope magnitude
    - SOS button state

    Later this can be replaced or extended with
    a trained ML fall-classification model.
    """

    def analyze(
        self,
        accel_x: float | None,
        accel_y: float | None,
        accel_z: float | None,
        gyro_x: float | None,
        gyro_y: float | None,
        gyro_z: float | None,
        sos_pressed: bool = False,
    ):

        ax = accel_x or 0.0
        ay = accel_y or 0.0
        az = accel_z or 0.0

        gx = gyro_x or 0.0
        gy = gyro_y or 0.0
        gz = gyro_z or 0.0


        acceleration_magnitude = math.sqrt(
            ax ** 2
            + ay ** 2
            + az ** 2
        )


        gyro_magnitude = math.sqrt(
            gx ** 2
            + gy ** 2
            + gz ** 2
        )


        # -----------------------------------------
        # MANUAL SOS
        # -----------------------------------------

        if sos_pressed:

            return {
                "fall_detected": False,
                "emergency_detected": True,
                "event_type": "MANUAL_SOS",
                "confidence": 1.0,
                "acceleration_magnitude": round(
                    acceleration_magnitude,
                    3,
                ),
                "gyro_magnitude": round(
                    gyro_magnitude,
                    3,
                ),
                "severity": "CRITICAL",
                "reason": "SOS button pressed",
            }


        # -----------------------------------------
        # STRONG FALL
        # -----------------------------------------

        if (
            acceleration_magnitude >= 18.0
            and gyro_magnitude >= 8.0
        ):

            return {
                "fall_detected": True,
                "emergency_detected": True,
                "event_type": "FALL_DETECTED",
                "confidence": 0.95,
                "acceleration_magnitude": round(
                    acceleration_magnitude,
                    3,
                ),
                "gyro_magnitude": round(
                    gyro_magnitude,
                    3,
                ),
                "severity": "CRITICAL",
                "reason": (
                    "High acceleration impact and "
                    "rapid orientation change detected"
                ),
            }


        # -----------------------------------------
        # POSSIBLE FALL
        # -----------------------------------------

        if (
            acceleration_magnitude >= 14.0
            and gyro_magnitude >= 5.0
        ):

            return {
                "fall_detected": True,
                "emergency_detected": False,
                "event_type": "POSSIBLE_FALL",
                "confidence": 0.7,
                "acceleration_magnitude": round(
                    acceleration_magnitude,
                    3,
                ),
                "gyro_magnitude": round(
                    gyro_magnitude,
                    3,
                ),
                "severity": "WARNING",
                "reason": (
                    "Unusual movement pattern detected"
                ),
            }


        # -----------------------------------------
        # NORMAL MOVEMENT
        # -----------------------------------------

        return {
            "fall_detected": False,
            "emergency_detected": False,
            "event_type": "NORMAL",
            "confidence": 0.95,
            "acceleration_magnitude": round(
                acceleration_magnitude,
                3,
            ),
            "gyro_magnitude": round(
                gyro_magnitude,
                3,
            ),
            "severity": "SAFE",
            "reason": "Normal movement pattern",
        }


fall_detection_service = FallDetectionService()