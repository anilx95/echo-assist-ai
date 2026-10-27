from collections import Counter, defaultdict, deque
from typing import Any


class ClassStabilizationService:
    """
    Stabilizes object classes across sequential frames.

    Example:
        Frame 1 -> bicycle
        Frame 2 -> bicycle
        Frame 3 -> motorcycle

    Stable result:
        bicycle

    History is stored separately for each track_id.
    """

    def __init__(
        self,
        history_size: int = 5,
        minimum_votes: int = 2,
    ):
        self.history_size = history_size
        self.minimum_votes = minimum_votes

        self.class_history = defaultdict(
            lambda: deque(
                maxlen=self.history_size
            )
        )


    def stabilize(
        self,
        objects: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        stabilized_objects = []

        for item in objects:

            tracking = item.get(
                "tracking",
                {},
            )

            detection = item.get(
                "detection",
                {},
            )

            track_id = tracking.get(
                "track_id"
            )

            raw_class = detection.get(
                "object_type",
                "unknown",
            )

            confidence = float(
                detection.get(
                    "confidence",
                    0.0,
                )
            )


            # ------------------------------------------
            # No track available
            # ------------------------------------------

            if track_id is None:

                item[
                    "class_stabilization"
                ] = {
                    "raw_class": raw_class,
                    "stable_class": raw_class,
                    "class_changed": False,
                    "history": [
                        raw_class
                    ],
                    "vote_count": 1,
                    "history_length": 1,
                    "stability_confidence": 1.0,
                    "status": "NO_TRACK_ID",
                }

                stabilized_objects.append(
                    item
                )

                continue


            # ------------------------------------------
            # Add class prediction to track history
            # ------------------------------------------

            history = self.class_history[
                track_id
            ]

            history.append(
                {
                    "class": raw_class,
                    "confidence": confidence,
                }
            )


            # ------------------------------------------
            # Count class votes
            # ------------------------------------------

            class_names = [
                entry["class"]
                for entry in history
            ]

            class_counts = Counter(
                class_names
            )

            most_common_class, vote_count = (
                class_counts.most_common(1)[0]
            )


            # ------------------------------------------
            # Resolve ties using confidence
            # ------------------------------------------

            highest_vote_count = max(
                class_counts.values()
            )

            tied_classes = [
                class_name
                for class_name, count
                in class_counts.items()
                if count == highest_vote_count
            ]


            if len(tied_classes) > 1:

                confidence_scores = {}

                for class_name in tied_classes:

                    scores = [
                        entry["confidence"]
                        for entry in history
                        if entry["class"]
                        == class_name
                    ]

                    confidence_scores[
                        class_name
                    ] = (
                        sum(scores)
                        / len(scores)
                    )


                most_common_class = max(
                    confidence_scores,
                    key=confidence_scores.get,
                )

                vote_count = class_counts[
                    most_common_class
                ]


            # ------------------------------------------
            # Stable class decision
            # ------------------------------------------

            if len(history) == 1:

                stable_class = raw_class

                status = (
                    "COLLECTING_HISTORY"
                )

            elif vote_count >= self.minimum_votes:

                stable_class = (
                    most_common_class
                )

                status = "STABILIZED"

            else:

                stable_class = raw_class

                status = (
                    "INSUFFICIENT_VOTES"
                )


            stability_confidence = round(
                vote_count / len(history),
                4,
            )


            # ------------------------------------------
            # Update detection class
            # ------------------------------------------

            class_changed = (
                stable_class != raw_class
            )

            detection[
                "raw_object_type"
            ] = raw_class

            detection[
                "object_type"
            ] = stable_class


            # ------------------------------------------
            # Add stabilization information
            # ------------------------------------------

            item[
                "class_stabilization"
            ] = {
                "raw_class": raw_class,

                "stable_class": (
                    stable_class
                ),

                "class_changed": (
                    class_changed
                ),

                "history": [
                    entry["class"]
                    for entry in history
                ],

                "vote_count": (
                    vote_count
                ),

                "history_length": len(
                    history
                ),

                "stability_confidence": (
                    stability_confidence
                ),

                "status": status,
            }


            stabilized_objects.append(
                item
            )


        return stabilized_objects


    def cleanup_tracks(
        self,
        active_track_ids: set[int],
    ) -> None:
        """
        Remove history belonging to tracks that are
        no longer active.
        """

        stored_track_ids = list(
            self.class_history.keys()
        )

        for track_id in stored_track_ids:

            if track_id not in active_track_ids:

                del self.class_history[
                    track_id
                ]


    def reset(self) -> None:
        """
        Reset all class histories.
        """

        self.class_history.clear()


class_stabilization_service = (
    ClassStabilizationService()
)