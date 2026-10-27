class GlobalSceneDecisionService:

    MIN_SAFE_WALKABILITY = 20.0
    DIRECTION_MARGIN = 3.0

    CRITICAL_DISTANCE_CM = 80.0
    NEAR_DISTANCE_CM = 150.0

    VEHICLE_TYPES = {
        "car",
        "bus",
        "truck",
        "motorcycle",
        "bicycle",
    }

    GROUND_HAZARDS = {
        "stairs",
        "pothole",
        "hole",
    }


    # ========================================================
    # GLOBAL SCENE DECISION
    # ========================================================

    def decide(
        self,
        pipeline_results: list,
        walkability: dict,
        sensor_fusion: dict,
    ) -> dict:

        if not pipeline_results:

            return self._no_object_decision(
                walkability=walkability,
                sensor_fusion=sensor_fusion,
            )


        # ----------------------------------------------------
        # WALKABILITY SCORES
        # ----------------------------------------------------

        left_score = float(
            walkability.get(
                "left_walkable_percent",
                0.0,
            )
        )

        center_score = float(
            walkability.get(
                "center_walkable_percent",
                0.0,
            )
        )

        right_score = float(
            walkability.get(
                "right_walkable_percent",
                0.0,
            )
        )


        path_scores = {
            "left": left_score,
            "center": center_score,
            "right": right_score,
        }


        safest_direction = max(
            path_scores,
            key=path_scores.get,
        )


        sorted_path_scores = sorted(
            path_scores.values(),
            reverse=True,
        )


        best_path_score = (
            sorted_path_scores[0]
        )

        second_best_score = (
            sorted_path_scores[1]
        )


        direction_margin = (
            best_path_score
            - second_best_score
        )


        # ----------------------------------------------------
        # ANALYSE ALL OBJECTS
        # ----------------------------------------------------

        threats = []

        direction_threat_counts = {
            "left": 0,
            "center": 0,
            "right": 0,
        }


        direction_nearest_distance = {
            "left": None,
            "center": None,
            "right": None,
        }


        for result in pipeline_results:

            detection = result.get(
                "detection",
                {},
            )

            distance_data = result.get(
                "distance_estimation",
                {},
            )

            risk_data = result.get(
                "risk_prediction",
                {},
            )

            decision_data = result.get(
                "decision",
                {},
            )


            object_type = str(
                detection.get(
                    "object_type",
                    "unknown",
                )
            ).lower()


            direction = str(
                detection.get(
                    "direction",
                    "center",
                )
            ).lower()


            if direction not in {
                "left",
                "center",
                "right",
            }:

                direction = "center"


            distance_cm = distance_data.get(
                "estimated_distance_cm"
            )


            risk_level = str(
                risk_data.get(
                    "risk_level",
                    "LOW",
                )
            ).upper()


            risk_confidence = float(
                risk_data.get(
                    "confidence",
                    0.0,
                )
            )


            priority = int(
                decision_data.get(
                    "priority",
                    4,
                )
            )


            # ----------------------------------------------
            # DIRECTION OCCUPANCY
            # ----------------------------------------------

            if (
                risk_level
                in {
                    "CRITICAL",
                    "HIGH",
                    "MEDIUM",
                }
            ):

                direction_threat_counts[
                    direction
                ] += 1


            # ----------------------------------------------
            # NEAREST DISTANCE PER DIRECTION
            # ----------------------------------------------

            if distance_cm is not None:

                current_nearest = (
                    direction_nearest_distance[
                        direction
                    ]
                )


                if (
                    current_nearest is None
                    or distance_cm
                    < current_nearest
                ):

                    direction_nearest_distance[
                        direction
                    ] = round(
                        float(distance_cm),
                        2,
                    )


            # ----------------------------------------------
            # THREAT SCORE
            # ----------------------------------------------

            threat_score = (
                self._calculate_threat_score(

                    object_type=object_type,

                    distance_cm=distance_cm,

                    risk_level=risk_level,

                    risk_confidence=(
                        risk_confidence
                    ),

                    direction=direction,

                    priority=priority,
                )
            )


            threats.append({

                "object_type": object_type,

                "direction": direction,

                "estimated_distance_cm": (
                    distance_cm
                ),

                "risk_level": risk_level,

                "risk_confidence": (
                    risk_confidence
                ),

                "priority": priority,

                "threat_score": (
                    threat_score
                ),
            })


        # ----------------------------------------------------
        # SORT MOST DANGEROUS FIRST
        # ----------------------------------------------------

        threats.sort(

            key=lambda item:
            item["threat_score"],

            reverse=True,
        )


        primary_threat = threats[0]


        critical_threats = [

            item

            for item in threats

            if item["risk_level"]
            == "CRITICAL"
        ]


        high_threats = [

            item

            for item in threats

            if item["risk_level"]
            == "HIGH"
        ]


        near_threats = [

            item

            for item in threats

            if (
                item[
                    "estimated_distance_cm"
                ]
                is not None

                and item[
                    "estimated_distance_cm"
                ]
                <= self.NEAR_DISTANCE_CM
            )
        ]


        center_near_threats = [

            item

            for item in near_threats

            if item["direction"]
            == "center"
        ]


        # ----------------------------------------------------
        # SENSOR CONFIDENCE
        # ----------------------------------------------------

        sensor_confidence = float(
            sensor_fusion.get(
                "confidence",
                0.0,
            )
        )


        sensor_status = str(
            sensor_fusion.get(
                "status",
                "UNKNOWN",
            )
        )


        # ====================================================
        # RULE 1: NO SAFE WALKABLE PATH
        # ====================================================

        if (
            best_path_score
            < self.MIN_SAFE_WALKABILITY
        ):

            return self._build_response(

                action="STOP",

                voice_message=(
                    "No safe walking path detected. "
                    "Stop and wait for a clear path."
                ),

                vibration=(
                    "STRONG_CONTINUOUS"
                ),

                priority=1,

                reason=(
                    "All path directions are below "
                    "the minimum walkability threshold."
                ),

                primary_threat=(
                    primary_threat
                ),

                threats=threats,

                safest_direction=(
                    safest_direction
                ),

                path_scores=path_scores,

                direction_threat_counts=(
                    direction_threat_counts
                ),

                direction_nearest_distance=(
                    direction_nearest_distance
                ),

                sensor_confidence=(
                    sensor_confidence
                ),

                sensor_status=(
                    sensor_status
                ),
            )


        # ====================================================
        # RULE 2: CRITICAL THREAT
        # ====================================================

        if critical_threats:

            return self._build_response(

                action="STOP",

                voice_message=(
                    "Immediate danger detected. "
                    "Stop now."
                ),

                vibration=(
                    "STRONG_CONTINUOUS"
                ),

                priority=1,

                reason=(
                    "At least one critical-risk "
                    "object is present."
                ),

                primary_threat=(
                    primary_threat
                ),

                threats=threats,

                safest_direction=(
                    safest_direction
                ),

                path_scores=path_scores,

                direction_threat_counts=(
                    direction_threat_counts
                ),

                direction_nearest_distance=(
                    direction_nearest_distance
                ),

                sensor_confidence=(
                    sensor_confidence
                ),

                sensor_status=(
                    sensor_status
                ),
            )


        # ====================================================
        # RULE 3: VERY CLOSE CENTER OBSTACLE
        # ====================================================

        critical_center = [

            item

            for item in center_near_threats

            if (
                item[
                    "estimated_distance_cm"
                ]
                is not None

                and item[
                    "estimated_distance_cm"
                ]
                <= self.CRITICAL_DISTANCE_CM
            )
        ]


        if critical_center:

            return self._build_response(

                action="STOP",

                voice_message=(
                    "Obstacle very close ahead. "
                    "Stop immediately."
                ),

                vibration=(
                    "STRONG_CONTINUOUS"
                ),

                priority=1,

                reason=(
                    "A center obstacle is inside "
                    "the critical distance threshold."
                ),

                primary_threat=(
                    primary_threat
                ),

                threats=threats,

                safest_direction=(
                    safest_direction
                ),

                path_scores=path_scores,

                direction_threat_counts=(
                    direction_threat_counts
                ),

                direction_nearest_distance=(
                    direction_nearest_distance
                ),

                sensor_confidence=(
                    sensor_confidence
                ),

                sensor_status=(
                    sensor_status
                ),
            )


        # ====================================================
        # RULE 4: MULTIPLE NEAR OBSTACLES + UNCERTAIN PATH
        # ====================================================

        if (
            len(near_threats) >= 3
            and direction_margin
            < self.DIRECTION_MARGIN
        ):

            return self._build_response(

                action="STOP",

                voice_message=(
                    "Multiple obstacles nearby. "
                    "Stop and wait for a safer path."
                ),

                vibration=(
                    "STRONG_CONTINUOUS"
                ),

                priority=1,

                reason=(
                    "Multiple nearby obstacles are "
                    "present and path scores are too "
                    "close for a reliable direction."
                ),

                primary_threat=(
                    primary_threat
                ),

                threats=threats,

                safest_direction=(
                    safest_direction
                ),

                path_scores=path_scores,

                direction_threat_counts=(
                    direction_threat_counts
                ),

                direction_nearest_distance=(
                    direction_nearest_distance
                ),

                sensor_confidence=(
                    sensor_confidence
                ),

                sensor_status=(
                    sensor_status
                ),
            )


        # ====================================================
        # RULE 5: CENTER HIGH-RISK THREAT
        # ====================================================

        center_high_threat = any(

            item["direction"] == "center"

            and item["risk_level"]
            in {
                "HIGH",
                "CRITICAL",
            }

            for item in threats
        )


        if center_high_threat:

            movement = (
                self._choose_safe_movement(

                    path_scores=path_scores,

                    threat_counts=(
                        direction_threat_counts
                    ),

                    nearest_distances=(
                        direction_nearest_distance
                    ),
                )
            )


            if movement is None:

                return self._build_response(

                    action="STOP",

                    voice_message=(
                        "Danger ahead and no reliable "
                        "escape direction is available. "
                        "Stop."
                    ),

                    vibration=(
                        "STRONG_CONTINUOUS"
                    ),

                    priority=1,

                    reason=(
                        "Center threat detected without "
                        "a sufficiently safe side path."
                    ),

                    primary_threat=(
                        primary_threat
                    ),

                    threats=threats,

                    safest_direction=(
                        safest_direction
                    ),

                    path_scores=path_scores,

                    direction_threat_counts=(
                        direction_threat_counts
                    ),

                    direction_nearest_distance=(
                        direction_nearest_distance
                    ),

                    sensor_confidence=(
                        sensor_confidence
                    ),

                    sensor_status=(
                        sensor_status
                    ),
                )


            action = (
                f"MOVE_{movement.upper()}"
            )


            return self._build_response(

                action=action,

                voice_message=(
                    f"Obstacle ahead. "
                    f"Safer path is on the "
                    f"{movement}. Move {movement}."
                ),

                vibration="MEDIUM",

                priority=2,

                reason=(
                    "High-risk center obstacle detected "
                    "and a safer side path is available."
                ),

                primary_threat=(
                    primary_threat
                ),

                threats=threats,

                safest_direction=(
                    movement
                ),

                path_scores=path_scores,

                direction_threat_counts=(
                    direction_threat_counts
                ),

                direction_nearest_distance=(
                    direction_nearest_distance
                ),

                sensor_confidence=(
                    sensor_confidence
                ),

                sensor_status=(
                    sensor_status
                ),
            )


        # ====================================================
        # RULE 6: HIGH THREAT EXISTS
        # ====================================================

        if high_threats:

            return self._build_response(

                action="SLOW_DOWN",

                voice_message=(
                    "Obstacle risk detected nearby. "
                    "Slow down and proceed carefully."
                ),

                vibration="MEDIUM",

                priority=2,

                reason=(
                    "One or more high-risk objects "
                    "are present."
                ),

                primary_threat=(
                    primary_threat
                ),

                threats=threats,

                safest_direction=(
                    safest_direction
                ),

                path_scores=path_scores,

                direction_threat_counts=(
                    direction_threat_counts
                ),

                direction_nearest_distance=(
                    direction_nearest_distance
                ),

                sensor_confidence=(
                    sensor_confidence
                ),

                sensor_status=(
                    sensor_status
                ),
            )


        # ====================================================
        # RULE 7: MEDIUM OR NEAR THREATS
        # ====================================================

        medium_exists = any(

            item["risk_level"]
            == "MEDIUM"

            for item in threats
        )


        if medium_exists or near_threats:

            return self._build_response(

                action="SLOW_DOWN",

                voice_message=(
                    "Nearby obstacles detected. "
                    "Slow down and continue carefully."
                ),

                vibration="LIGHT",

                priority=3,

                reason=(
                    "Medium-risk or nearby objects "
                    "are present."
                ),

                primary_threat=(
                    primary_threat
                ),

                threats=threats,

                safest_direction=(
                    safest_direction
                ),

                path_scores=path_scores,

                direction_threat_counts=(
                    direction_threat_counts
                ),

                direction_nearest_distance=(
                    direction_nearest_distance
                ),

                sensor_confidence=(
                    sensor_confidence
                ),

                sensor_status=(
                    sensor_status
                ),
            )


        # ====================================================
        # RULE 8: CLEAR SCENE
        # ====================================================

        return self._build_response(

            action="CONTINUE",

            voice_message=(
                "Path appears clear. "
                "Continue carefully."
            ),

            vibration="NONE",

            priority=4,

            reason=(
                "No significant scene-level "
                "threat was detected."
            ),

            primary_threat=(
                primary_threat
            ),

            threats=threats,

            safest_direction=(
                safest_direction
            ),

            path_scores=path_scores,

            direction_threat_counts=(
                direction_threat_counts
            ),

            direction_nearest_distance=(
                direction_nearest_distance
            ),

            sensor_confidence=(
                sensor_confidence
            ),

            sensor_status=(
                sensor_status
            ),
        )


    # ========================================================
    # THREAT SCORE
    # ========================================================

    def _calculate_threat_score(
        self,
        object_type,
        distance_cm,
        risk_level,
        risk_confidence,
        direction,
        priority,
    ):

        risk_scores = {
            "CRITICAL": 100.0,
            "HIGH": 75.0,
            "MEDIUM": 45.0,
            "LOW": 15.0,
        }


        score = risk_scores.get(
            risk_level,
            10.0,
        )


        # Center obstacles matter more.

        if direction == "center":
            score += 15.0


        # Close objects matter more.

        if distance_cm is not None:

            if distance_cm <= 80:
                score += 30.0

            elif distance_cm <= 150:
                score += 20.0

            elif distance_cm <= 300:
                score += 10.0


        # Vehicles get additional attention.

        if object_type in self.VEHICLE_TYPES:
            score += 10.0


        # Ground hazards get strong weighting.

        if object_type in self.GROUND_HAZARDS:
            score += 25.0


        # Decision priority contribution.

        score += max(
            0,
            5 - priority,
        ) * 3.0


        # Risk confidence contribution.

        score += (
            risk_confidence
            * 10.0
        )


        return round(
            score,
            2,
        )


    # ========================================================
    # CHOOSE SAFE MOVEMENT DIRECTION
    # ========================================================

    def _choose_safe_movement(
        self,
        path_scores,
        threat_counts,
        nearest_distances,
    ):

        candidates = []


        for direction in [
            "left",
            "right",
        ]:

            walkability = (
                path_scores[
                    direction
                ]
            )


            if (
                walkability
                < self.MIN_SAFE_WALKABILITY
            ):

                continue


            threat_count = (
                threat_counts[
                    direction
                ]
            )


            nearest_distance = (
                nearest_distances[
                    direction
                ]
            )


            clearance_bonus = 0.0


            if nearest_distance is None:

                clearance_bonus = 20.0

            else:

                clearance_bonus = min(
                    nearest_distance / 50.0,
                    20.0,
                )


            safety_score = (

                walkability

                - (
                    threat_count
                    * 5.0
                )

                + clearance_bonus
            )


            candidates.append({

                "direction": direction,

                "safety_score": (
                    safety_score
                ),
            })


        if not candidates:
            return None


        candidates.sort(

            key=lambda item:
            item["safety_score"],

            reverse=True,
        )


        best = candidates[0]


        return best[
            "direction"
        ]


    # ========================================================
    # NO OBJECT DECISION
    # ========================================================

    def _no_object_decision(
        self,
        walkability,
        sensor_fusion,
    ):

        scores = {

            "left": float(
                walkability.get(
                    "left_walkable_percent",
                    0.0,
                )
            ),

            "center": float(
                walkability.get(
                    "center_walkable_percent",
                    0.0,
                )
            ),

            "right": float(
                walkability.get(
                    "right_walkable_percent",
                    0.0,
                )
            ),
        }


        safest_direction = max(
            scores,
            key=scores.get,
        )


        best_score = scores[
            safest_direction
        ]


        if (
            best_score
            < self.MIN_SAFE_WALKABILITY
        ):

            action = "STOP"

            voice_message = (
                "No safe walking path detected. "
                "Please stop."
            )

            vibration = (
                "STRONG_CONTINUOUS"
            )

            priority = 1

            reason = (
                "No detected object, but path "
                "segmentation found no safe path."
            )


        else:

            action = "CONTINUE"

            voice_message = (
                "Path appears clear. "
                "Continue carefully."
            )

            vibration = "NONE"

            priority = 4

            reason = (
                "No objects detected and a "
                "walkable path is available."
            )


        return self._build_response(

            action=action,

            voice_message=voice_message,

            vibration=vibration,

            priority=priority,

            reason=reason,

            primary_threat=None,

            threats=[],

            safest_direction=(
                safest_direction
            ),

            path_scores=scores,

            direction_threat_counts={
                "left": 0,
                "center": 0,
                "right": 0,
            },

            direction_nearest_distance={
                "left": None,
                "center": None,
                "right": None,
            },

            sensor_confidence=float(
                sensor_fusion.get(
                    "confidence",
                    0.0,
                )
            ),

            sensor_status=str(
                sensor_fusion.get(
                    "status",
                    "UNKNOWN",
                )
            ),
        )


    # ========================================================
    # STANDARD RESPONSE BUILDER
    # ========================================================

    def _build_response(
        self,
        action,
        voice_message,
        vibration,
        priority,
        reason,
        primary_threat,
        threats,
        safest_direction,
        path_scores,
        direction_threat_counts,
        direction_nearest_distance,
        sensor_confidence,
        sensor_status,
    ):

        return {

            "action": action,

            "voice_message": (
                voice_message
            ),

            "vibration": vibration,

            "priority": priority,

            "reason": reason,

            "primary_threat": (
                primary_threat
            ),

            "threat_count": len(
                threats
            ),

            "critical_threat_count": len([

                item

                for item in threats

                if item["risk_level"]
                == "CRITICAL"
            ]),

            "high_threat_count": len([

                item

                for item in threats

                if item["risk_level"]
                == "HIGH"
            ]),

            "safest_direction": (
                safest_direction
            ),

            "path_scores": (
                path_scores
            ),

            "direction_threat_counts": (
                direction_threat_counts
            ),

            "direction_nearest_distance_cm": (
                direction_nearest_distance
            ),

            "sensor_confidence": (
                sensor_confidence
            ),

            "sensor_status": (
                sensor_status
            ),
        }


global_scene_decision_service = (
    GlobalSceneDecisionService()
)