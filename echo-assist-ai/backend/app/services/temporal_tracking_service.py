import math
import time
import statistics
from collections import defaultdict, deque


class TemporalTrackingService:

    def __init__(self):

        self.next_track_id = 1

        self.tracks = {}

        self.distance_history = defaultdict(
            lambda: deque(maxlen=10)
        )

        # ====================================================
        # MATCHING CONFIGURATION
        # ====================================================

        self.minimum_match_score = 0.32

        self.max_center_distance_ratio = 2.0

        self.max_distance_difference_ratio = 0.85

        self.minimum_iou_gate = 0.0

        # Number of sequential API frames a track can disappear
        # before it is removed.
        self.max_missed_frames = 5

        # Backup cleanup for abandoned sessions.
        self.track_timeout_seconds = 300.0

        self.current_frame_number = 0


    # ========================================================
    # BOX HELPERS
    # ========================================================

    def get_box_center(
        self,
        bounding_box,
    ):

        x1 = float(
            bounding_box["x1"]
        )

        y1 = float(
            bounding_box["y1"]
        )

        x2 = float(
            bounding_box["x2"]
        )

        y2 = float(
            bounding_box["y2"]
        )

        return (
            (x1 + x2) / 2.0,
            (y1 + y2) / 2.0,
        )


    def get_box_size(
        self,
        bounding_box,
    ):

        width = max(
            1.0,
            float(
                bounding_box["x2"]
            )
            - float(
                bounding_box["x1"]
            ),
        )

        height = max(
            1.0,
            float(
                bounding_box["y2"]
            )
            - float(
                bounding_box["y1"]
            ),
        )

        return width, height


    def get_box_area(
        self,
        bounding_box,
    ):

        width, height = (
            self.get_box_size(
                bounding_box
            )
        )

        return width * height


    def calculate_center_distance(
        self,
        center_a,
        center_b,
    ):

        dx = (
            center_a[0]
            - center_b[0]
        )

        dy = (
            center_a[1]
            - center_b[1]
        )

        return math.sqrt(
            dx * dx
            + dy * dy
        )


    def calculate_iou(
        self,
        box_a,
        box_b,
    ):

        ax1 = float(box_a["x1"])
        ay1 = float(box_a["y1"])
        ax2 = float(box_a["x2"])
        ay2 = float(box_a["y2"])

        bx1 = float(box_b["x1"])
        by1 = float(box_b["y1"])
        bx2 = float(box_b["x2"])
        by2 = float(box_b["y2"])

        intersection_x1 = max(
            ax1,
            bx1,
        )

        intersection_y1 = max(
            ay1,
            by1,
        )

        intersection_x2 = min(
            ax2,
            bx2,
        )

        intersection_y2 = min(
            ay2,
            by2,
        )

        intersection_width = max(
            0.0,
            intersection_x2
            - intersection_x1,
        )

        intersection_height = max(
            0.0,
            intersection_y2
            - intersection_y1,
        )

        intersection_area = (
            intersection_width
            * intersection_height
        )

        area_a = max(
            0.0,
            (ax2 - ax1)
            * (ay2 - ay1),
        )

        area_b = max(
            0.0,
            (bx2 - bx1)
            * (by2 - by1),
        )

        union_area = (
            area_a
            + area_b
            - intersection_area
        )

        if union_area <= 0:
            return 0.0

        return (
            intersection_area
            / union_area
        )


    def calculate_size_similarity(
        self,
        box_a,
        box_b,
    ):

        area_a = self.get_box_area(
            box_a
        )

        area_b = self.get_box_area(
            box_b
        )

        larger_area = max(
            area_a,
            area_b,
        )

        if larger_area <= 0:
            return 0.0

        return (
            min(
                area_a,
                area_b,
            )
            / larger_area
        )


    # ========================================================
    # CLASS FAMILY HANDLING
    # ========================================================

    def normalize_object_type(
        self,
        object_type,
    ):

        object_type = (
            str(object_type)
            .lower()
            .strip()
        )

        class_groups = {

            "bicycle": "two_wheeler",

            "motorcycle": "two_wheeler",

            "motorbike": "two_wheeler",

            "bike": "two_wheeler",


            "car": "road_vehicle",

            "bus": "road_vehicle",

            "truck": "road_vehicle",
        }

        return class_groups.get(
            object_type,
            object_type,
        )


    def calculate_class_score(
        self,
        old_object_type,
        new_object_type,
    ):

        old_type = (
            str(old_object_type)
            .lower()
            .strip()
        )

        new_type = (
            str(new_object_type)
            .lower()
            .strip()
        )

        # Exact class match
        if old_type == new_type:
            return 1.0

        old_group = (
            self.normalize_object_type(
                old_type
            )
        )

        new_group = (
            self.normalize_object_type(
                new_type
            )
        )

        # Related class family
        if old_group == new_group:
            return 0.75

        return 0.0


    # ========================================================
    # POSITION PREDICTION
    # ========================================================

    def predict_track_center(
        self,
        track,
    ):

        current_center = track[
            "center"
        ]

        previous_center = track.get(
            "previous_center"
        )

        if previous_center is None:
            return current_center

        velocity_x = (
            current_center[0]
            - previous_center[0]
        )

        velocity_y = (
            current_center[1]
            - previous_center[1]
        )

        predicted_center = (

            current_center[0]
            + velocity_x,

            current_center[1]
            + velocity_y,
        )

        return predicted_center


    # ========================================================
    # TRACK CLEANUP
    # ========================================================

    def cleanup_expired_tracks(
        self,
        current_time,
    ):

        expired_track_ids = []

        for (
            track_id,
            track,
        ) in self.tracks.items():

            time_age = (
                current_time
                - track["last_seen"]
            )

            missed_frames = track.get(
                "missed_frames",
                0,
            )

            if (
                time_age
                > self.track_timeout_seconds
                or missed_frames
                > self.max_missed_frames
            ):

                expired_track_ids.append(
                    track_id
                )


        for track_id in expired_track_ids:

            self.tracks.pop(
                track_id,
                None,
            )

            self.distance_history.pop(
                track_id,
                None,
            )


    # ========================================================
    # MATCH SCORE
    # ========================================================

    def calculate_match_score(
        self,
        track,
        detection,
        center,
        bounding_box,
        estimated_distance_cm,
    ):

        old_box = track[
            "bounding_box"
        ]

        predicted_center = (
            self.predict_track_center(
                track
            )
        )


        # ----------------------------------------------------
        # CENTER DISTANCE
        # ----------------------------------------------------

        center_distance = (
            self.calculate_center_distance(
                center,
                predicted_center,
            )
        )


        old_width, old_height = (
            self.get_box_size(
                old_box
            )
        )

        new_width, new_height = (
            self.get_box_size(
                bounding_box
            )
        )


        reference_scale = max(

            old_width,

            old_height,

            new_width,

            new_height,

            1.0,
        )


        normalized_center_distance = (
            center_distance
            / reference_scale
        )


        # Hard geometry rejection
        if (
            normalized_center_distance
            > self.max_center_distance_ratio
        ):

            return None


        center_score = max(
            0.0,

            1.0
            - (
                normalized_center_distance
                / self.max_center_distance_ratio
            ),
        )


        # ----------------------------------------------------
        # IOU
        # ----------------------------------------------------

        iou_score = (
            self.calculate_iou(
                old_box,
                bounding_box,
            )
        )


        # ----------------------------------------------------
        # SIZE SIMILARITY
        # ----------------------------------------------------

        size_score = (
            self.calculate_size_similarity(
                old_box,
                bounding_box,
            )
        )


        # Reject extreme size changes unless boxes overlap.
        if (
            size_score < 0.08
            and iou_score <= 0.0
        ):

            return None


        # ----------------------------------------------------
        # DISTANCE SIMILARITY
        # ----------------------------------------------------

        distance_score = 0.5

        old_distance = track.get(
            "last_distance_cm"
        )


        if (
            old_distance is not None
            and estimated_distance_cm
            is not None
        ):

            old_distance = float(
                old_distance
            )

            new_distance = float(
                estimated_distance_cm
            )


            reference_distance = max(

                old_distance,

                new_distance,

                1.0,
            )


            difference_ratio = (

                abs(
                    old_distance
                    - new_distance
                )

                / reference_distance
            )


            if (
                difference_ratio
                > self.max_distance_difference_ratio
            ):

                return None


            distance_score = max(

                0.0,

                1.0
                - (
                    difference_ratio
                    / self.max_distance_difference_ratio
                ),
            )


        # ----------------------------------------------------
        # CLASS COMPATIBILITY
        # ----------------------------------------------------

        class_score = (
            self.calculate_class_score(

                track["object_type"],

                detection[
                    "object_type"
                ],
            )
        )


        # Different unrelated class
        if class_score <= 0.0:
            return None


        # ----------------------------------------------------
        # FINAL SCORE
        # ----------------------------------------------------

        match_score = (

            center_score * 0.30

            + iou_score * 0.25

            + size_score * 0.15

            + distance_score * 0.15

            + class_score * 0.15
        )


        return {
            "score": min(
                1.0,
                match_score,
            ),

            "center_score": (
                center_score
            ),

            "iou_score": (
                iou_score
            ),

            "size_score": (
                size_score
            ),

            "distance_score": (
                distance_score
            ),

            "class_score": (
                class_score
            ),
        }


    # ========================================================
    # BUILD GLOBAL MATCH CANDIDATES
    # ========================================================

    def build_match_candidates(
        self,
        objects,
    ):

        candidates = []


        for object_index, item in enumerate(
            objects
        ):

            detection = item[
                "detection"
            ]

            bounding_box = detection[
                "bounding_box"
            ]

            center = self.get_box_center(
                bounding_box
            )

            distance_data = item.get(
                "distance_estimation",
                {},
            )

            estimated_distance_cm = (
                distance_data.get(
                    "estimated_distance_cm"
                )
            )


            for (
                track_id,
                track,
            ) in self.tracks.items():


                match_data = (
                    self.calculate_match_score(

                        track=track,

                        detection=detection,

                        center=center,

                        bounding_box=bounding_box,

                        estimated_distance_cm=(
                            estimated_distance_cm
                        ),
                    )
                )


                if match_data is None:
                    continue


                score = match_data[
                    "score"
                ]


                if (
                    score
                    < self.minimum_match_score
                ):
                    continue


                candidates.append({

                    "object_index": (
                        object_index
                    ),

                    "track_id": (
                        track_id
                    ),

                    "score": (
                        score
                    ),

                    "match_data": (
                        match_data
                    ),
                })


        # Highest confidence assignments first
        candidates.sort(

            key=lambda candidate:
            candidate["score"],

            reverse=True,
        )


        return candidates


    # ========================================================
    # GLOBAL ONE-TO-ONE ASSIGNMENT
    # ========================================================

    def assign_tracks(
        self,
        objects,
    ):

        candidates = (
            self.build_match_candidates(
                objects
            )
        )


        assigned_objects = {}

        used_track_ids = set()


        for candidate in candidates:

            object_index = candidate[
                "object_index"
            ]

            track_id = candidate[
                "track_id"
            ]


            if (
                object_index
                in assigned_objects
            ):
                continue


            if (
                track_id
                in used_track_ids
            ):
                continue


            assigned_objects[
                object_index
            ] = candidate


            used_track_ids.add(
                track_id
            )


        return (
            assigned_objects,
            used_track_ids,
        )


    # ========================================================
    # CREATE TRACK
    # ========================================================

    def create_track(
        self,
        detection,
        center,
        estimated_distance_cm,
        timestamp,
    ):

        track_id = (
            self.next_track_id
        )

        self.next_track_id += 1


        self.tracks[
            track_id
        ] = {

            "track_id": (
                track_id
            ),

            "object_type": detection[
                "object_type"
            ],

            "center": center,

            "previous_center": None,

            "bounding_box": detection[
                "bounding_box"
            ],

            "last_seen": timestamp,

            "last_frame_number": (
                self.current_frame_number
            ),

            "frames_seen": 1,

            "missed_frames": 0,

            "last_distance_cm": (

                float(
                    estimated_distance_cm
                )

                if estimated_distance_cm
                is not None

                else None
            ),
        }


        if (
            estimated_distance_cm
            is not None
        ):

            self.distance_history[
                track_id
            ].append({

                "timestamp": timestamp,

                "distance_cm": float(
                    estimated_distance_cm
                ),
            })


        return track_id


    # ========================================================
    # UPDATE TRACK
    # ========================================================

    def update_existing_track(
        self,
        track_id,
        detection,
        center,
        estimated_distance_cm,
        timestamp,
    ):

        track = self.tracks[
            track_id
        ]


        track[
            "previous_center"
        ] = track[
            "center"
        ]


        track[
            "center"
        ] = center


        track[
            "bounding_box"
        ] = detection[
            "bounding_box"
        ]


        track[
            "last_seen"
        ] = timestamp


        track[
            "last_frame_number"
        ] = self.current_frame_number


        track[
            "frames_seen"
        ] += 1


        track[
            "missed_frames"
        ] = 0


        # Keep latest raw class.
        # Class stabilization handles historical voting.
        track[
            "object_type"
        ] = detection[
            "object_type"
        ]


        if (
            estimated_distance_cm
            is not None
        ):

            track[
                "last_distance_cm"
            ] = float(
                estimated_distance_cm
            )


            self.distance_history[
                track_id
            ].append({

                "timestamp": timestamp,

                "distance_cm": float(
                    estimated_distance_cm
                ),
            })


    # ========================================================
    # MARK UNMATCHED TRACKS
    # ========================================================

    def mark_missed_tracks(
        self,
        matched_track_ids,
    ):

        for (
            track_id,
            track,
        ) in self.tracks.items():

            if (
                track_id
                not in matched_track_ids
            ):

                track[
                    "missed_frames"
                ] = (
                    track.get(
                        "missed_frames",
                        0,
                    )
                    + 1
                )


    # ========================================================
    # MOTION ANALYSIS
    # ========================================================

    def analyze_motion(
        self,
        track_id,
    ):

        history = list(self.distance_history[track_id])

        if len(history) < 3:
            return {
                "motion_status": "INSUFFICIENT_DATA",
                "approach_speed_cm_s": 0.0,
                "distance_change_cm": 0.0,
                "time_to_collision_s": None,
                "raw_distance_cm": round(float(history[-1]["distance_cm"]), 2) if history else None,
                "smoothed_distance_cm": None,
                "motion_samples_used": len(history),
            }

        recent = history[-5:]
        distances = [float(x["distance_cm"]) for x in recent]
        median_distance = statistics.median(distances)
        allowed_jump = max(20.0, median_distance * 0.35)
        filtered = [x for x in recent if abs(float(x["distance_cm"]) - median_distance) <= allowed_jump]
        if len(filtered) < 2:
            filtered = recent

        base_time = filtered[0]["timestamp"]
        times = [x["timestamp"] - base_time for x in filtered]
        values = [float(x["distance_cm"]) for x in filtered]
        mean_t = statistics.mean(times)
        mean_d = statistics.mean(values)
        denominator = sum((t - mean_t) ** 2 for t in times)

        if denominator <= 0:
            return {
                "motion_status": "UNKNOWN",
                "approach_speed_cm_s": 0.0,
                "distance_change_cm": 0.0,
                "time_to_collision_s": None,
                "raw_distance_cm": round(distances[-1], 2),
                "smoothed_distance_cm": round(statistics.median(values[-3:]), 2),
                "motion_samples_used": len(filtered),
            }

        slope = sum((times[i] - mean_t) * (values[i] - mean_d) for i in range(len(values))) / denominator
        approach_speed = -slope
        distance_change = values[0] - values[-1]

        if approach_speed > 8.0:
            motion_status = "APPROACHING"
        elif approach_speed < -8.0:
            motion_status = "MOVING_AWAY"
        else:
            motion_status = "STATIONARY"

        smoothed_distance = statistics.median(values[-3:])
        ttc = None
        if motion_status == "APPROACHING" and approach_speed > 0:
            candidate = smoothed_distance / approach_speed
            if 0 < candidate <= 120:
                ttc = candidate

        return {
            "motion_status": motion_status,
            "approach_speed_cm_s": round(approach_speed, 2),
            "distance_change_cm": round(distance_change, 2),
            "time_to_collision_s": round(ttc, 2) if ttc is not None else None,
            "raw_distance_cm": round(distances[-1], 2),
            "smoothed_distance_cm": round(smoothed_distance, 2),
            "motion_samples_used": len(filtered),
        }


    # ========================================================
    # PROCESS FRAME
    # ========================================================

    def process_frame(
        self,
        objects,
        timestamp=None,
    ):

        if timestamp is None:
            timestamp = time.time()


        self.current_frame_number += 1


        self.cleanup_expired_tracks(
            timestamp
        )


        (
            assignments,
            matched_existing_track_ids,
        ) = self.assign_tracks(
            objects
        )


        tracked_results = []

        active_track_ids = set()


        for object_index, item in enumerate(
            objects
        ):

            detection = item[
                "detection"
            ]

            bounding_box = detection[
                "bounding_box"
            ]


            center = (
                self.get_box_center(
                    bounding_box
                )
            )


            distance_data = item.get(
                "distance_estimation",
                {},
            )


            estimated_distance_cm = (
                distance_data.get(
                    "estimated_distance_cm"
                )
            )


            assignment = assignments.get(
                object_index
            )


            if assignment is None:

                track_id = (
                    self.create_track(

                        detection=detection,

                        center=center,

                        estimated_distance_cm=(
                            estimated_distance_cm
                        ),

                        timestamp=timestamp,
                    )
                )


                match_status = (
                    "NEW_TRACK"
                )


                match_confidence = 1.0


                match_details = {

                    "center_score": None,

                    "iou_score": None,

                    "size_score": None,

                    "distance_score": None,

                    "class_score": None,
                }


            else:

                track_id = assignment[
                    "track_id"
                ]


                self.update_existing_track(

                    track_id=track_id,

                    detection=detection,

                    center=center,

                    estimated_distance_cm=(
                        estimated_distance_cm
                    ),

                    timestamp=timestamp,
                )


                match_status = (
                    "MATCHED"
                )


                match_confidence = (
                    assignment[
                        "score"
                    ]
                )


                match_details = (
                    assignment[
                        "match_data"
                    ]
                )


            active_track_ids.add(
                track_id
            )


            motion_analysis = (
                self.analyze_motion(
                    track_id
                )
            )


            tracked_results.append({

                **item,

                "tracking": {

                    "track_id": (
                        track_id
                    ),

                    "frames_seen": (
                        self.tracks[
                            track_id
                        ][
                            "frames_seen"
                        ]
                    ),

                    "match_status": (
                        match_status
                    ),

                    "match_confidence": round(
                        float(
                            match_confidence
                        ),
                        4,
                    ),

                    "missed_frames": (
                        self.tracks[
                            track_id
                        ][
                            "missed_frames"
                        ]
                    ),

                    "tracker_frame_number": (
                        self.current_frame_number
                    ),

                    "match_details": {

                        key: (

                            round(
                                float(value),
                                4,
                            )

                            if value
                            is not None

                            else None
                        )

                        for key, value
                        in match_details.items()

                        if key != "score"
                    },

                    **motion_analysis,
                },
            })


        # Mark old tracks that were not matched in this frame.
        #
        # New tracks are included in active_track_ids,
        # so they are not marked as missed.

        matched_or_created_ids = (
            active_track_ids
        )


        self.mark_missed_tracks(
            matched_track_ids=(
                matched_or_created_ids
            )
        )


        self.cleanup_expired_tracks(
            timestamp
        )


        return tracked_results


    # ========================================================
    # GET ACTIVE TRACK IDS
    # ========================================================

    def get_active_track_ids(
        self,
    ):

        return set(
            self.tracks.keys()
        )


    # ========================================================
    # RESET TRACKER
    # ========================================================

    def reset(
        self,
    ):

        self.tracks.clear()

        self.distance_history.clear()

        self.next_track_id = 1

        self.current_frame_number = 0


# ============================================================
# GLOBAL SERVICE INSTANCE
# ============================================================

temporal_tracking_service = (
    TemporalTrackingService()
)