class MotionRiskService:

    # ========================================================
    # MOTION-AWARE RISK ESCALATION
    # ========================================================

    def evaluate(
        self,
        risk_result: dict,
        tracking_result: dict,
    ) -> dict:

        updated_risk = dict(risk_result)

        original_level = str(
            risk_result.get(
                "risk_level",
                "LOW",
            )
        ).upper()

        motion_status = str(
            tracking_result.get(
                "motion_status",
                "INSUFFICIENT_DATA",
            )
        ).upper()

        approach_speed = float(
            tracking_result.get(
                "approach_speed_cm_s",
                0.0,
            )
            or 0.0
        )

        time_to_collision = (
            tracking_result.get(
                "time_to_collision_s"
            )
        )


        updated_risk[
            "original_risk_level"
        ] = original_level

        updated_risk[
            "motion_risk_escalated"
        ] = False

        updated_risk[
            "motion_risk_reason"
        ] = (
            "No motion-based escalation required."
        )


        # ====================================================
        # RULE 1:
        # IMMINENT COLLISION
        # TTC <= 1.5 seconds
        # ====================================================

        if (
            time_to_collision is not None
            and time_to_collision <= 1.5
        ):

            updated_risk[
                "risk_level"
            ] = "CRITICAL"

            updated_risk[
                "risk_class"
            ] = 3

            updated_risk[
                "motion_risk_escalated"
            ] = True

            updated_risk[
                "motion_risk_reason"
            ] = (
                "Imminent collision detected. "
                f"Estimated time to collision is "
                f"{round(time_to_collision, 2)} seconds."
            )

            return updated_risk


        # ====================================================
        # RULE 2:
        # FAST APPROACHING OBJECT
        # ====================================================

        if (
            motion_status == "APPROACHING"
            and approach_speed >= 100.0
        ):

            if original_level in [
                "LOW",
                "MEDIUM",
            ]:

                updated_risk[
                    "risk_level"
                ] = "HIGH"

                updated_risk[
                    "risk_class"
                ] = 2

                updated_risk[
                    "motion_risk_escalated"
                ] = True

                updated_risk[
                    "motion_risk_reason"
                ] = (
                    "Object is approaching rapidly at "
                    f"{round(approach_speed, 1)} "
                    "centimeters per second."
                )

            return updated_risk


        # ====================================================
        # RULE 3:
        # APPROACHING OBJECT WITH SHORT TTC
        # ====================================================

        if (
            motion_status == "APPROACHING"
            and time_to_collision is not None
            and time_to_collision <= 3.0
        ):

            if original_level == "LOW":

                updated_risk[
                    "risk_level"
                ] = "MEDIUM"

                updated_risk[
                    "risk_class"
                ] = 1


            elif original_level == "MEDIUM":

                updated_risk[
                    "risk_level"
                ] = "HIGH"

                updated_risk[
                    "risk_class"
                ] = 2


            updated_risk[
                "motion_risk_escalated"
            ] = True

            updated_risk[
                "motion_risk_reason"
            ] = (
                "Approaching object has a short "
                f"time to collision of "
                f"{round(time_to_collision, 2)} seconds."
            )

            return updated_risk


        # ====================================================
        # RULE 4:
        # OBJECT MOVING AWAY
        #
        # Do not reduce ML risk automatically.
        # Safety system remains conservative.
        # ====================================================

        if motion_status == "MOVING_AWAY":

            updated_risk[
                "motion_risk_reason"
            ] = (
                "Object is moving away. "
                "Original risk level retained for safety."
            )


        return updated_risk


motion_risk_service = MotionRiskService()