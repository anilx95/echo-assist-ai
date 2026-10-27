from pathlib import Path

import cv2
from ultralytics import YOLO


class ObjectDetectionService:

    def __init__(self):
        print("Loading YOLO11 Nano for backend...")

        self.model = YOLO("yolo11n.pt")

        print("YOLO11 Nano backend service ready.")


    def calculate_direction(
        self,
        x1,
        x2,
        frame_width,
    ):
        object_center = (x1 + x2) / 2

        left_limit = frame_width / 3
        right_limit = (frame_width * 2) / 3

        if object_center < left_limit:
            return "left"

        if object_center > right_limit:
            return "right"

        return "center"


    def detect_image(self, image_path):

        frame = cv2.imread(str(image_path))

        if frame is None:
            raise ValueError(
                "Unable to read uploaded image"
            )

        height, width = frame.shape[:2]

        results = self.model(
            frame,
            verbose=False
        )

        detections = []

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])

                confidence = float(box.conf[0])

                object_type = self.model.names[
                    class_id
                ]

                x1, y1, x2, y2 = (
                    box.xyxy[0]
                    .cpu()
                    .tolist()
                )

                direction = self.calculate_direction(
                    x1=x1,
                    x2=x2,
                    frame_width=width,
                )

                detections.append({
                    "object_type": object_type,

                    "confidence": round(
                        confidence,
                        4
                    ),

                    "direction": direction,

                    "bounding_box": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2),
                    },
                })

        return detections


object_detection_service = ObjectDetectionService()