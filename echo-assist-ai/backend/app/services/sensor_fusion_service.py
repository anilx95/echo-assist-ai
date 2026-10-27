from typing import Optional


class SensorFusionService:
    """
    Combines ToF and ultrasonic distance readings.

    ToF weight: 60%
    Ultrasonic weight: 40%
    """

    def fuse_distance(
        self,
        tof_mm: Optional[float],
        ultrasonic_cm: Optional[float],
    ) -> dict:

        # No sensor data
        if tof_mm is None and ultrasonic_cm is None:
            return {
                "distance_cm": None,
                "confidence": 0.0,
                "status": "NO_DATA",
                "tof_cm": None,
                "ultrasonic_cm": None,
            }

        # Convert ToF millimetres to centimetres
        tof_cm = tof_mm / 10.0 if tof_mm is not None else None

        # Only ToF available
        if tof_cm is not None and ultrasonic_cm is None:
            return {
                "distance_cm": round(tof_cm, 2),
                "confidence": 0.60,
                "status": "TOF_ONLY",
                "tof_cm": round(tof_cm, 2),
                "ultrasonic_cm": None,
            }

        # Only ultrasonic available
        if ultrasonic_cm is not None and tof_cm is None:
            return {
                "distance_cm": round(ultrasonic_cm, 2),
                "confidence": 0.50,
                "status": "ULTRASONIC_ONLY",
                "tof_cm": None,
                "ultrasonic_cm": round(ultrasonic_cm, 2),
            }

        # Both sensors available
        difference = abs(tof_cm - ultrasonic_cm)

        if difference <= 10:
            confidence = 0.99
            status = "HIGH_CONFIDENCE"

        elif difference <= 25:
            confidence = 0.90
            status = "GOOD_CONFIDENCE"

        elif difference <= 50:
            confidence = 0.75
            status = "MEDIUM_CONFIDENCE"

        else:
            confidence = 0.50
            status = "SENSOR_DISAGREEMENT"

        fused_distance = (
            tof_cm * 0.60
            + ultrasonic_cm * 0.40
        )

        return {
            "distance_cm": round(fused_distance, 2),
            "confidence": confidence,
            "status": status,
            "tof_cm": round(tof_cm, 2),
            "ultrasonic_cm": round(ultrasonic_cm, 2),
            "sensor_difference_cm": round(difference, 2),
        }


sensor_fusion_service = SensorFusionService()