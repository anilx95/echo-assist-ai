import sys
import time
import getpass
import threading
from queue import Queue, Empty, Full
import msvcrt

import cv2
import requests


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "http://127.0.0.1:8000"

LOGIN_URL = f"{BASE_URL}/auth/login"

REALTIME_FRAME_URL = (
    f"{BASE_URL}/ai/pipeline/realtime-frame"
)

RESET_URL = (
    f"{BASE_URL}/ai/pipeline/realtime/reset"
)


CAMERA_INDEX = 0

FRAME_WIDTH = 640

FRAME_HEIGHT = 480

JPEG_QUALITY = 75

CAPTURE_INTERVAL_SECONDS = 0.5

REQUEST_TIMEOUT_SECONDS = 120


# ============================================================
# LOGIN
# ============================================================

def login(
    email: str,
    password: str,
) -> str:

    print("\nLogging in...")

    try:

        response = requests.post(
            LOGIN_URL,
            json={
                "email": email,
                "password": password,
            },
            timeout=30,
        )

    except requests.RequestException as exc:

        raise RuntimeError(
            f"Could not connect to backend: {exc}"
        ) from exc


    if response.status_code != 200:

        raise RuntimeError(
            "Login failed.\n"
            f"Status: {response.status_code}\n"
            f"Response: {response.text}"
        )


    data = response.json()

    access_token = data.get(
        "access_token"
    )


    if not access_token:

        raise RuntimeError(
            "Login response does not contain access_token."
        )


    print("Login successful.")

    return access_token


# ============================================================
# RESET REAL-TIME SESSION
# ============================================================

def reset_realtime_session(
    headers: dict,
):

    print(
        "\nResetting real-time session..."
    )

    try:

        response = requests.post(
            RESET_URL,
            headers=headers,
            timeout=30,
        )

    except requests.RequestException as exc:

        print(
            f"Warning: reset failed: {exc}"
        )

        return


    if response.status_code == 200:

        print(
            "Real-time session reset successfully."
        )

    else:

        print(
            "Warning: reset request failed."
        )

        print(
            response.text
        )


# ============================================================
# OPEN CAMERA
# ============================================================

def open_camera():

    print(
        f"\nOpening camera index {CAMERA_INDEX}..."
    )


    camera = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW,
    )


    if not camera.isOpened():

        print(
            "DirectShow failed. Trying default backend..."
        )

        camera.release()

        camera = cv2.VideoCapture(
            CAMERA_INDEX
        )


    if not camera.isOpened():

        raise RuntimeError(
            "Could not open camera."
        )


    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        FRAME_WIDTH,
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        FRAME_HEIGHT,
    )


    print(
        "Camera opened successfully."
    )

    return camera


# ============================================================
# ENCODE FRAME
# ============================================================

def encode_frame(
    frame,
):

    success, encoded = cv2.imencode(
        ".jpg",
        frame,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            JPEG_QUALITY,
        ],
    )


    if not success:

        raise RuntimeError(
            "Could not encode frame."
        )


    return encoded.tobytes()


# ============================================================
# SEND ONE FRAME
# ============================================================

def send_frame(
    frame,
    headers: dict,
):

    image_bytes = encode_frame(
        frame
    )


    files = {
        "file": (
            "camera_frame.jpg",
            image_bytes,
            "image/jpeg",
        )
    }


    params = {
        "speed": 0,
        "surface_risk": 0,
        "lighting_risk": 0,
    }


    try:

        response = requests.post(
            REALTIME_FRAME_URL,
            headers=headers,
            files=files,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    except requests.RequestException as exc:

        return {
            "pipeline_status": "REQUEST_ERROR",
            "error": str(exc),
        }


    if response.status_code != 200:

        return {
            "pipeline_status": "HTTP_ERROR",
            "status_code": response.status_code,
            "error": response.text,
        }


    try:

        return response.json()

    except ValueError:

        return {
            "pipeline_status":
                "INVALID_JSON_RESPONSE",

            "error":
                response.text,
        }


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_result(
    result: dict,
):

    pipeline_status = result.get(
        "pipeline_status",
        "UNKNOWN",
    )


    if pipeline_status == "FRAME_SKIPPED":

        print(
            "\nFrame skipped by backend."
        )

        return


    if pipeline_status in {
        "REQUEST_ERROR",
        "HTTP_ERROR",
        "INVALID_JSON_RESPONSE",
    }:

        print(
            "\nPipeline request failed:"
        )

        print(
            result
        )

        return


    realtime = result.get(
        "realtime",
        {},
    )


    frame_number = realtime.get(
        "frame_number",
        "?",
    )


    objects_detected = result.get(
        "objects_detected",
        0,
    )


    # --------------------------------------------------------
    # RAW SCENE DECISION
    # --------------------------------------------------------

    scene_decision = result.get(
        "scene_decision",
        {},
    )


    raw_action = scene_decision.get(
        "action",
        "UNKNOWN",
    )


    scene_reason = scene_decision.get(
        "reason",
        "No reason provided.",
    )


    path_scores = scene_decision.get(
        "path_scores",
        {},
    )


    safest_direction = scene_decision.get(
        "safest_direction",
        "unknown",
    )


    threat_count = scene_decision.get(
        "threat_count",
        0,
    )


    critical_count = scene_decision.get(
        "critical_threat_count",
        0,
    )


    high_count = scene_decision.get(
        "high_threat_count",
        0,
    )


    # --------------------------------------------------------
    # STABILIZED DECISION
    # --------------------------------------------------------

    stabilized_decision = result.get(
        "stabilized_scene_decision",
        {},
    )


    stable_action = stabilized_decision.get(
        "action",
        "UNKNOWN",
    )


    command_stabilization = (
        stabilized_decision.get(
            "command_stabilization",
            {},
        )
    )


    stabilization_status = (
        command_stabilization.get(
            "status",
            "UNKNOWN",
        )
    )


    pending_action = (
        command_stabilization.get(
            "pending_action"
        )
    )


    confirmation_count = (
        command_stabilization.get(
            "confirmation_count",
            0,
        )
    )


    confirmation_required = (
        command_stabilization.get(
            "confirmation_required",
            0,
        )
    )


    # --------------------------------------------------------
    # CANE OUTPUT
    # --------------------------------------------------------

    cane_output = result.get(
        "cane_output",
        {},
    )


    cane_action = cane_output.get(
        "action",
        "UNKNOWN",
    )


    voice_output = cane_output.get(
        "voice_output",
        {},
    )


    voice_message = voice_output.get(
        "message",
        "",
    )


    hardware_commands = cane_output.get(
        "hardware_commands",
        {},
    )


    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    print(
        "\n"
        "============================================================"
    )

    print(
        f"FRAME NUMBER        : {frame_number}"
    )

    print(
        f"PIPELINE STATUS     : {pipeline_status}"
    )

    print(
        f"OBJECTS DETECTED    : {objects_detected}"
    )

    print(
        "------------------------------------------------------------"
    )

    print(
        f"RAW ACTION          : {raw_action}"
    )

    print(
        f"STABLE ACTION       : {stable_action}"
    )

    print(
        f"STABILIZER STATUS   : {stabilization_status}"
    )

    print(
        f"PENDING ACTION      : {pending_action}"
    )

    print(
        f"CONFIRMATION        : "
        f"{confirmation_count}/{confirmation_required}"
    )

    print(
        "------------------------------------------------------------"
    )

    print(
        f"SCENE REASON        : {scene_reason}"
    )

    print(
        f"PATH SCORES         : {path_scores}"
    )

    print(
        f"SAFEST DIRECTION    : {safest_direction}"
    )

    print(
        f"THREAT COUNT        : {threat_count}"
    )

    print(
        f"CRITICAL THREATS    : {critical_count}"
    )

    print(
        f"HIGH THREATS        : {high_count}"
    )

    print(
        "------------------------------------------------------------"
    )

    print(
        f"CANE ACTION         : {cane_action}"
    )

    print(
        f"VOICE MESSAGE       : {voice_message}"
    )

    print(
        f"HARDWARE COMMANDS   : {hardware_commands}"
    )

    print(
        "============================================================"
    )


# ============================================================
# SHARED STATE
# ============================================================

class SharedState:

    def __init__(self):

        self.lock = threading.Lock()

        self.latest_result = {}

        self.worker_busy = False

        self.stop_event = threading.Event()


    def set_result(
        self,
        result: dict,
    ):

        with self.lock:

            self.latest_result = result


    def get_result(
        self,
    ):

        with self.lock:

            return self.latest_result.copy()


    def set_worker_busy(
        self,
        value: bool,
    ):

        with self.lock:

            self.worker_busy = value


    def is_worker_busy(
        self,
    ):

        with self.lock:

            return self.worker_busy


# ============================================================
# BACKGROUND AI WORKER
# ============================================================

def ai_worker(
    frame_queue: Queue,
    headers: dict,
    shared_state: SharedState,
):

    print(
        "AI background worker started."
    )


    while not shared_state.stop_event.is_set():

        try:

            frame = frame_queue.get(
                timeout=0.2
            )

        except Empty:

            continue


        if frame is None:

            frame_queue.task_done()

            break


        shared_state.set_worker_busy(
            True
        )


        try:

            print(
                "\nSending frame to AI pipeline..."
            )


            result = send_frame(
                frame=frame,
                headers=headers,
            )


            display_result(
                result
            )


            if result.get(
                "pipeline_status"
            ) not in {

                "REQUEST_ERROR",

                "HTTP_ERROR",

                "INVALID_JSON_RESPONSE",

                "FRAME_SKIPPED",

            }:

                shared_state.set_result(
                    result
                )


        except Exception as exc:

            print(
                f"\nAI worker error: {exc}"
            )


        finally:

            shared_state.set_worker_busy(
                False
            )

            frame_queue.task_done()


    print(
        "AI background worker stopped."
    )


# ============================================================
# DRAW CAMERA STATUS
# ============================================================

def draw_status(
    frame,
    latest_result: dict,
    worker_busy: bool,
):

    display_frame = frame.copy()


    if worker_busy:

        processing_text = "AI: PROCESSING"

    else:

        processing_text = "AI: READY"


    cv2.putText(
        display_frame,
        processing_text,
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )


    if not latest_result:

        cv2.putText(
            display_frame,
            "Waiting for first AI result...",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )


    else:

        scene_decision = latest_result.get(
            "scene_decision",
            {},
        )


        stabilized = latest_result.get(
            "stabilized_scene_decision",
            {},
        )


        cane_output = latest_result.get(
            "cane_output",
            {},
        )


        raw_action = scene_decision.get(
            "action",
            "UNKNOWN",
        )


        stable_action = stabilized.get(
            "action",
            "UNKNOWN",
        )


        cane_action = cane_output.get(
            "action",
            "UNKNOWN",
        )


        command_stabilization = (
            stabilized.get(
                "command_stabilization",
                {},
            )
        )


        status = command_stabilization.get(
            "status",
            "UNKNOWN",
        )


        cv2.putText(
            display_frame,
            f"Raw: {raw_action}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )


        cv2.putText(
            display_frame,
            f"Stable: {stable_action}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )


        cv2.putText(
            display_frame,
            f"Status: {status}",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )


        cv2.putText(
            display_frame,
            f"Cane: {cane_action}",
            (20, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )


    cv2.putText(
        display_frame,
        "Press Q to quit",
        (20, 220),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )


    return display_frame


# ============================================================
# PUT LATEST FRAME INTO QUEUE
# ============================================================

def queue_latest_frame(
    frame_queue: Queue,
    frame,
):

    try:

        frame_queue.put_nowait(
            frame.copy()
        )

        return True


    except Full:

        # Remove stale waiting frame

        try:

            old_frame = frame_queue.get_nowait()

            frame_queue.task_done()

            del old_frame

        except Empty:

            pass


        try:

            frame_queue.put_nowait(
                frame.copy()
            )

            return True

        except Full:

            return False


# ============================================================
# REAL-TIME CAMERA PIPELINE
# ============================================================

def run_camera_pipeline(
    access_token: str,
):

    headers = {
        "Authorization":
            f"Bearer {access_token}"
    }


    reset_realtime_session(
        headers=headers
    )


    camera = open_camera()


    # Queue size 1 prevents old frames from building up.

    frame_queue = Queue(
        maxsize=1
    )


    shared_state = SharedState()


    worker_thread = threading.Thread(
        target=ai_worker,
        args=(
            frame_queue,
            headers,
            shared_state,
        ),
        daemon=True,
    )


    worker_thread.start()


    last_capture_time = 0.0


    print(
        "\nReal-time camera pipeline started."
    )

    print(
        "Press Q in the camera window to stop."
    )

    print(
        "You can also press Ctrl+C in this terminal."
    )


    try:

        while True:

            success, frame = camera.read()


            if not success:

                print(
                    "Failed to read camera frame."
                )

                time.sleep(
                    0.05
                )

                continue


            current_time = time.time()


            # ------------------------------------------------
            # QUEUE FRAME WITHOUT BLOCKING CAMERA WINDOW
            # ------------------------------------------------

            if (
                current_time
                - last_capture_time
                >= CAPTURE_INTERVAL_SECONDS
            ):

                queue_latest_frame(
                    frame_queue=frame_queue,
                    frame=frame,
                )


                last_capture_time = (
                    current_time
                )


            # ------------------------------------------------
            # READ LATEST AI RESULT
            # ------------------------------------------------

            latest_result = (
                shared_state.get_result()
            )


            worker_busy = (
                shared_state.is_worker_busy()
            )


            # ------------------------------------------------
            # DISPLAY CAMERA
            # ------------------------------------------------

            display_frame = draw_status(
                frame=frame,
                latest_result=latest_result,
                worker_busy=worker_busy,
            )


            cv2.imshow(
                "ECHO-ASSIST AI Real-Time Camera",
                display_frame,
            )


                        # ========================================================
            # KEYBOARD EXIT HANDLING
            # ========================================================

            # OpenCV camera-window keyboard input
            key = cv2.waitKey(10) & 0xFF

            if key == ord("q") or key == ord("Q"):

                print(
                    "\nQ pressed in camera window. "
                    "Stopping camera pipeline..."
                )

                break


            # Windows PowerShell / terminal keyboard input
            if msvcrt.kbhit():

                terminal_key = msvcrt.getwch()

                if terminal_key.lower() == "q":

                    print(
                        "\nQ pressed in terminal. "
                        "Stopping camera pipeline..."
                    )

                    break

            # Also stop if user closes the window.

            try:

                window_visible = cv2.getWindowProperty(
                    "ECHO-ASSIST AI Real-Time Camera",
                    cv2.WND_PROP_VISIBLE,
                )


                if window_visible < 1:

                    print(
                        "\nCamera window closed."
                    )

                    break

            except cv2.error:

                break


    except KeyboardInterrupt:

        print(
            "\nCtrl+C detected. Stopping..."
        )


    finally:

        # Signal worker to stop.

        shared_state.stop_event.set()


        # Clear waiting frames.

        while True:

            try:

                frame_queue.get_nowait()

                frame_queue.task_done()

            except Empty:

                break


        # Tell worker to exit if possible.

        try:

            frame_queue.put_nowait(
                None
            )

        except Full:

            pass


        camera.release()

        cv2.destroyAllWindows()


        print(
            "Camera released successfully."
        )


        print(
            "Waiting briefly for AI worker shutdown..."
        )


        worker_thread.join(
            timeout=2.0
        )


        if worker_thread.is_alive():

            print(
                "AI request is still finishing in background. "
                "Main camera client is closing."
            )

        else:

            print(
                "AI worker stopped successfully."
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "============================================================"
    )

    print(
        "ECHO-ASSIST AI - REAL-TIME CAMERA CLIENT"
    )

    print(
        "============================================================"
    )


    email = input(
        "\nEmail: "
    ).strip()


    password = getpass.getpass(
        "Password: "
    )


    if not email or not password:

        print(
            "Email and password are required."
        )

        sys.exit(1)


    try:

        access_token = login(
            email=email,
            password=password,
        )


        run_camera_pipeline(
            access_token=access_token
        )


    except KeyboardInterrupt:

        print(
            "\nProgram stopped."
        )


    except Exception as exc:

        print(
            f"\nCamera client error: {exc}"
        )

        sys.exit(1)


if __name__ == "__main__":

    main()