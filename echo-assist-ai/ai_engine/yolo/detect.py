from pathlib import Path

import cv2
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

OUTPUT_DIR.mkdir(exist_ok=True)


class EchoObjectDetector:

    def __init__(self):
        print("Loading YOLO11 Nano model...")

        self.model = YOLO("yolo11n.pt")

        print("YOLO11 Nano loaded successfully.")


    def calculate_direction(
        self,
        box,
        frame_width,
    ):
        x1, y1, x2, y2 = box

        center_x = (x1 + x2) / 2

        left_boundary = frame_width / 3
        right_boundary = (frame_width * 2) / 3

        if center_x < left_boundary:
            return "left"

        elif center_x > right_boundary:
            return "right"

        return "center"


    def detect_frame(self, frame):

        results = self.model(
            frame,
            verbose=False
        )

        detections = []

        frame_height, frame_width = frame.shape[:2]

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])

                confidence = float(box.conf[0])

                object_name = self.model.names[class_id]

                coordinates = box.xyxy[0].tolist()

                direction = self.calculate_direction(
                    coordinates,
                    frame_width
                )

                detections.append({
                    "object_type": object_name,
                    "confidence": round(
                        confidence,
                        4
                    ),
                    "direction": direction,
                    "bounding_box": {
                        "x1": round(coordinates[0], 2),
                        "y1": round(coordinates[1], 2),
                        "x2": round(coordinates[2], 2),
                        "y2": round(coordinates[3], 2),
                    }
                })

        return detections


if __name__ == "__main__":

    detector = EchoObjectDetector()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Camera could not be opened.")
        raise SystemExit(1)

    print("ECHO-ASSIST AI Object Detection Started")
    print("Press Q to stop.")

    while True:

        success, frame = camera.read()

        if not success:
            print("Failed to read camera frame.")
            break

        detections = detector.detect_frame(frame)

        for detection in detections:

            print(
                detection["object_type"],
                "| Confidence:",
                detection["confidence"],
                "| Direction:",
                detection["direction"]
            )

        results = detector.model(
            frame,
            verbose=False
        )

        annotated_frame = results[0].plot()

        cv2.imshow(
            "ECHO-ASSIST AI - YOLO11",
            annotated_frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()

    cv2.destroyAllWindows()