"""Short-lived per-user realtime frame state.

This is deliberately marked as transient. Redis can replace this adapter when
the application runs with multiple workers; users must never share a camera
session in a single process.
"""

import time
from collections import deque
from threading import Lock


class RealtimePipelineService:
    def __init__(self):
        self._sessions: dict[int, dict] = {}
        self._lock = Lock()

    def _session(self, user_id: int) -> dict:
        with self._lock:
            return self._sessions.setdefault(user_id, {
                "frame_number": 0, "last_processed_time": 0.0,
                "frame_history": deque(maxlen=30), "latest_result": None,
            })

    def should_process_frame(self, user_id: int, minimum_interval_seconds: float = 0.3) -> bool:
        session = self._session(user_id)
        now = time.time()
        if now - session["last_processed_time"] < minimum_interval_seconds:
            return False
        session["last_processed_time"] = now
        return True

    def start_frame(self, user_id: int) -> dict:
        session = self._session(user_id)
        session["frame_number"] += 1
        return {"frame_number": session["frame_number"], "timestamp": time.time()}

    def store_result(self, user_id: int, result: dict) -> dict:
        session = self._session(user_id)
        record = {
            "frame_number": session["frame_number"], "timestamp": time.time(),
            "scene_action": result.get("scene_decision", {}).get("action"),
            "objects_detected": result.get("objects_detected", 0), "result": result,
        }
        session["frame_history"].append(record)
        session["latest_result"] = result
        return record

    def get_latest_result(self, user_id: int):
        return self._session(user_id)["latest_result"]

    def get_history(self, user_id: int, limit: int = 10):
        return list(self._session(user_id)["frame_history"])[-limit:]

    def reset(self, user_id: int) -> None:
        with self._lock:
            self._sessions.pop(user_id, None)


realtime_pipeline_service = RealtimePipelineService()
