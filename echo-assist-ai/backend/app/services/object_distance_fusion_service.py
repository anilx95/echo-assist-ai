import math


class ObjectDistanceFusionService:

    # ========================================================
    # ESTIMATE PER-OBJECT DISTANCES
    # ========================================================

    def estimate_distances(
        self,
        objects,
        physical_distance_cm,
    ):
        """
        Estimate a separate distance for every detected object.

        MiDaS output is treated as relative inverse depth:
        larger depth value usually means closer.

        The nearest valid-depth object is anchored to the
        physical ToF + ultrasonic fused distance.

        Other objects are estimated relative to that anchor.
        """

        if not objects:
            return []


        if (
            physical_distance_cm is None
            or physical_distance_cm <= 0
        ):

            return self._depth_only_fallback(
                objects
            )


        valid_objects = [

            item

            for item in objects

            if item.get("relative_depth") is not None
            and math.isfinite(
                item["relative_depth"]
            )
            and item["relative_depth"] > 0
        ]


        # ----------------------------------------------------
        # NO VALID MIDAS DEPTH
        # ----------------------------------------------------

        if not valid_objects:

            return [

                {
                    **item,

                    "estimated_distance_cm": round(
                        physical_distance_cm,
                        2,
                    ),

                    "distance_source": (
                        "physical_sensor_fallback"
                    ),

                    "depth_rank": "unknown",

                    "distance_confidence": 0.50,
                }

                for item in objects
            ]


        # ----------------------------------------------------
        # FIND CLOSEST OBJECT
        # ----------------------------------------------------
        #
        # MiDaS inverse depth:
        # higher value = generally closer
        #

        closest_depth = max(

            item["relative_depth"]

            for item in valid_objects
        )


        sorted_depths = sorted(

            [
                item["relative_depth"]
                for item in valid_objects
            ],

            reverse=True,
        )


        results = []


        for item in objects:

            depth = item.get(
                "relative_depth"
            )


            # ------------------------------------------------
            # INVALID DEPTH FALLBACK
            # ------------------------------------------------

            if (
                depth is None
                or not math.isfinite(depth)
                or depth <= 0
            ):

                results.append({

                    **item,

                    "estimated_distance_cm": round(
                        physical_distance_cm,
                        2,
                    ),

                    "distance_source": (
                        "physical_sensor_fallback"
                    ),

                    "depth_rank": "unknown",

                    "distance_confidence": 0.50,
                })

                continue


            # ------------------------------------------------
            # RELATIVE DISTANCE ESTIMATION
            # ------------------------------------------------
            #
            # inverse depth ratio:
            #
            # estimated distance =
            # sensor distance × closest depth / object depth
            #

            depth_ratio = (
                closest_depth / depth
            )


            estimated_distance = (
                physical_distance_cm
                * depth_ratio
            )


            # Prevent unrealistic explosion from noisy depth.

            maximum_distance = max(
                physical_distance_cm * 8.0,
                1000.0,
            )


            estimated_distance = min(

                estimated_distance,

                maximum_distance,
            )


            estimated_distance = max(

                estimated_distance,

                physical_distance_cm,
            )


            # ------------------------------------------------
            # DEPTH RANK
            # ------------------------------------------------

            rank_index = sorted_depths.index(
                depth
            )


            total = len(
                sorted_depths
            )


            if total == 1:

                depth_rank = "nearest"


            elif rank_index == 0:

                depth_rank = "nearest"


            elif rank_index == total - 1:

                depth_rank = "farthest"


            else:

                depth_rank = "middle"


            # ------------------------------------------------
            # CONFIDENCE
            # ------------------------------------------------

            if depth_rank == "nearest":

                confidence = 0.85

            else:

                confidence = 0.65


            results.append({

                **item,

                "estimated_distance_cm": round(
                    estimated_distance,
                    2,
                ),

                "distance_source": (
                    "midas_relative_depth_"
                    "plus_physical_sensor_anchor"
                ),

                "depth_rank": depth_rank,

                "distance_confidence": confidence,
            })


        return results


    # ========================================================
    # DEPTH-ONLY FALLBACK
    # ========================================================

    def _depth_only_fallback(
        self,
        objects,
    ):

        valid_depths = [

            item.get("relative_depth")

            for item in objects

            if item.get("relative_depth") is not None
            and item.get("relative_depth") > 0
        ]


        if not valid_depths:

            return [

                {
                    **item,

                    "estimated_distance_cm": None,

                    "distance_source": (
                        "unavailable"
                    ),

                    "depth_rank": "unknown",

                    "distance_confidence": 0.0,
                }

                for item in objects
            ]


        maximum_depth = max(
            valid_depths
        )


        minimum_depth = min(
            valid_depths
        )


        results = []


        for item in objects:

            depth = item.get(
                "relative_depth"
            )


            if depth is None or depth <= 0:

                rank = "unknown"

            elif depth == maximum_depth:

                rank = "nearest"

            elif depth == minimum_depth:

                rank = "farthest"

            else:

                rank = "middle"


            results.append({

                **item,

                "estimated_distance_cm": None,

                "distance_source": (
                    "midas_depth_rank_only"
                ),

                "depth_rank": rank,

                "distance_confidence": 0.35,
            })


        return results


object_distance_fusion_service = (
    ObjectDistanceFusionService()
)