import time
from collections import deque
from threading import Lock


class RealtimePipelineService:

    def __init__(self):

        self.frame_number = 0

        self.last_processed_time = 0.0

        self.processing_lock = Lock()

        self.frame_history = deque(
            maxlen=30
        )

        self.latest_result = None


    # ========================================================
    # CHECK IF FRAME SHOULD BE PROCESSED
    # ========================================================

    def should_process_frame(
        self,
        minimum_interval_seconds: float = 0.3,
    ) -> bool:

        current_time = time.time()

        elapsed = (
            current_time
            - self.last_processed_time
        )

        if elapsed < minimum_interval_seconds:

            return False

        self.last_processed_time = (
            current_time
        )

        return True


    # ========================================================
    # START FRAME
    # ========================================================

    def start_frame(self):

        self.frame_number += 1

        return {
            "frame_number": self.frame_number,
            "timestamp": time.time(),
        }


    # ========================================================
    # STORE FRAME RESULT
    # ========================================================

    def store_result(
        self,
        result: dict,
    ):

        frame_record = {

            "frame_number": (
                self.frame_number
            ),

            "timestamp": time.time(),

            "scene_action": (
                result
                .get(
                    "scene_decision",
                    {},
                )
                .get(
                    "action"
                )
            ),

            "objects_detected": (
                result.get(
                    "objects_detected",
                    0,
                )
            ),

            "result": result,
        }


        self.frame_history.append(
            frame_record
        )


        self.latest_result = result


        return frame_record


    # ========================================================
    # GET LATEST RESULT
    # ========================================================

    def get_latest_result(self):

        return self.latest_result


    # ========================================================
    # GET RECENT FRAME HISTORY
    # ========================================================

    def get_history(
        self,
        limit: int = 10,
    ):

        history = list(
            self.frame_history
        )

        return history[
            -limit:
        ]


    # ========================================================
    # RESET REAL-TIME SESSION
    # ========================================================

    def reset(self):

        self.frame_number = 0

        self.last_processed_time = 0.0

        self.frame_history.clear()

        self.latest_result = None


realtime_pipeline_service = (
    RealtimePipelineService()
)