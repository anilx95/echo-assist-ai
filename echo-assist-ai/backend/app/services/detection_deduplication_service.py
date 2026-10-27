class DetectionDeduplicationService:

    def __init__(self):

        self.iou_threshold = 0.55

        self.class_groups = {
            "bicycle": "two_wheeler",
            "motorcycle": "two_wheeler",
            "motorbike": "two_wheeler",
            "bike": "two_wheeler",
        }


    def normalize_class(
        self,
        object_type: str,
    ) -> str:

        object_type = (
            str(object_type)
            .lower()
            .strip()
        )

        return self.class_groups.get(
            object_type,
            object_type,
        )


    def calculate_iou(
        self,
        box_a: dict,
        box_b: dict,
    ) -> float:

        x_left = max(
            box_a["x1"],
            box_b["x1"],
        )

        y_top = max(
            box_a["y1"],
            box_b["y1"],
        )

        x_right = min(
            box_a["x2"],
            box_b["x2"],
        )

        y_bottom = min(
            box_a["y2"],
            box_b["y2"],
        )


        if (
            x_right <= x_left
            or y_bottom <= y_top
        ):
            return 0.0


        intersection = (
            (x_right - x_left)
            *
            (y_bottom - y_top)
        )


        area_a = (
            (box_a["x2"] - box_a["x1"])
            *
            (box_a["y2"] - box_a["y1"])
        )


        area_b = (
            (box_b["x2"] - box_b["x1"])
            *
            (box_b["y2"] - box_b["y1"])
        )


        union = (
            area_a
            + area_b
            - intersection
        )


        if union <= 0:
            return 0.0


        return float(
            intersection / union
        )


    def deduplicate(
        self,
        detections: list,
    ) -> list:

        if not detections:
            return []


        sorted_detections = sorted(
            detections,
            key=lambda item: item.get(
                "confidence",
                0.0,
            ),
            reverse=True,
        )


        kept = []


        for candidate in sorted_detections:

            candidate_type = (
                self.normalize_class(
                    candidate.get(
                        "object_type",
                        "unknown",
                    )
                )
            )


            candidate_box = candidate.get(
                "bounding_box"
            )


            if not candidate_box:

                kept.append(candidate)

                continue


            duplicate_found = False


            for existing in kept:

                existing_type = (
                    self.normalize_class(
                        existing.get(
                            "object_type",
                            "unknown",
                        )
                    )
                )


                if (
                    candidate_type
                    != existing_type
                ):
                    continue


                existing_box = existing.get(
                    "bounding_box"
                )


                if not existing_box:
                    continue


                iou = self.calculate_iou(
                    candidate_box,
                    existing_box,
                )


                if (
                    iou
                    >= self.iou_threshold
                ):

                    duplicate_found = True

                    break


            if not duplicate_found:

                kept.append(candidate)


        return kept


detection_deduplication_service = (
    DetectionDeduplicationService()
)