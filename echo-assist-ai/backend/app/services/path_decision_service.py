class PathDecisionService:

    MIN_WALKABLE_PERCENT = 20.0
    MIN_DIRECTION_MARGIN = 3.0

    def refine_decision(
        self,
        decision: dict,
        walkability: dict,
    ) -> dict:

        original_action = decision["action"]

        left = walkability[
            "left_walkable_percent"
        ]

        center = walkability[
            "center_walkable_percent"
        ]

        right = walkability[
            "right_walkable_percent"
        ]

        scores = {
            "left": left,
            "center": center,
            "right": right,
        }

        safest_direction = max(
            scores,
            key=scores.get
        )

        sorted_scores = sorted(
            scores.values(),
            reverse=True
        )

        best_score = sorted_scores[0]
        second_best = sorted_scores[1]

        margin = best_score - second_best


        # No sufficiently walkable path
        if best_score < self.MIN_WALKABLE_PERCENT:

            return {
                **decision,

                "action": "STOP",

                "voice_message": (
                    "No safe path detected. "
                    "Please stop."
                ),

                "vibration": "STRONG",

                "priority": 1,

                "path_override": True,

                "path_reason": (
                    "No direction meets the "
                    "minimum walkability threshold."
                ),
            }


        # Scores are too close to make a reliable turn decision
        if margin < self.MIN_DIRECTION_MARGIN:

            if original_action in [
                "MOVE_LEFT",
                "MOVE_RIGHT",
            ]:

                return {
                    **decision,

                    "action": "SLOW_DOWN",

                    "voice_message": (
                        "Obstacle detected. "
                        "Path confidence is low. "
                        "Slow down and proceed carefully."
                    ),

                    "vibration": "MEDIUM",

                    "priority": 2,

                    "path_override": True,

                    "path_reason": (
                        "Walkability scores are "
                        "too close for a reliable "
                        "direction change."
                    ),
                }


        # Original decision says move right,
        # but right is not the safest path
        if (
            original_action == "MOVE_RIGHT"
            and safest_direction != "right"
        ):

            return {
                **decision,

                "action": (
                    f"MOVE_{safest_direction.upper()}"
                ),

                "voice_message": (
                    f"Safer path detected on the "
                    f"{safest_direction}. "
                    f"Move {safest_direction}."
                ),

                "vibration": "MEDIUM",

                "priority": 2,

                "path_override": True,

                "path_reason": (
                    "Fast-SCNN changed the "
                    "movement direction."
                ),
            }


        # Original decision says move left,
        # but left is not the safest path
        if (
            original_action == "MOVE_LEFT"
            and safest_direction != "left"
        ):

            return {
                **decision,

                "action": (
                    f"MOVE_{safest_direction.upper()}"
                ),

                "voice_message": (
                    f"Safer path detected on the "
                    f"{safest_direction}. "
                    f"Move {safest_direction}."
                ),

                "vibration": "MEDIUM",

                "priority": 2,

                "path_override": True,

                "path_reason": (
                    "Fast-SCNN changed the "
                    "movement direction."
                ),
            }


        return {
            **decision,

            "path_override": False,

            "path_reason": (
                "Original decision agrees with "
                "walkable path analysis."
            ),
        }


path_decision_service = PathDecisionService()