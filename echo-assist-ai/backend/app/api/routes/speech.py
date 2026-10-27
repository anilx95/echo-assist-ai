import os
import shutil
import tempfile

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

from app.schemas.speech import (
    AudioCommandResponse,
    AudioNavigationResponse,
    VoiceCommandRequest,
    VoiceCommandResponse,
    VoiceNavigationRequest,
    VoiceNavigationResponse,
)

from app.services.auth_service import get_current_user
from app.services.navigation_service import navigation_service
from app.services.speech_service import speech_service
from app.services.whisper_service import whisper_service
from app.services.emergency_service import emergency_service

from app.services.notification_service import (
    NotificationService,
    get_notification_service,
)


router = APIRouter(
    prefix="/speech",
    tags=["speech"],
)


ALLOWED_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".ogg",
    ".webm",
}


# ============================================================
# HELPER: SAVE AUDIO TEMPORARILY
# ============================================================

def save_temp_audio(audio: UploadFile):

    original_filename = audio.filename or "audio.wav"

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    if extension not in ALLOWED_AUDIO_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. "
                "Use WAV, MP3, M4A, OGG, or WEBM."
            ),
        )

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension,
    ) as temp_file:

        shutil.copyfileobj(
            audio.file,
            temp_file,
        )

        return temp_file.name


# ============================================================
# HELPER: TRIGGER VOICE EMERGENCY
# ============================================================

def trigger_voice_emergency(
    db: Session,
    current_user: User,
    notifier: NotificationService,
    latitude: float | None = None,
    longitude: float | None = None,
):

    return emergency_service.trigger_emergency(
        db=db,
        user=current_user,
        notifier=notifier,
        event_type="VOICE_SOS",
        latitude=latitude,
        longitude=longitude,
    )


# ============================================================
# 1. BASIC TEXT COMMAND
# ============================================================

@router.post(
    "/command",
    response_model=VoiceCommandResponse,
)
def process_voice_command(

    payload: VoiceCommandRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

    notifier: NotificationService = Depends(
        get_notification_service
    ),
):

    result = speech_service.parse_command(
        payload.text
    )


    # --------------------------------------------------------
    # EMERGENCY COMMAND
    # --------------------------------------------------------

    if result["intent"] == "EMERGENCY":

        event = trigger_voice_emergency(
            db=db,
            current_user=current_user,
            notifier=notifier,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )

        result["response"] = (
            f"Emergency alert activated. "
            f"Emergency ID {event.id}."
        )


    return VoiceCommandResponse(
        **result
    )


# ============================================================
# 2. TEXT COMMAND → REAL NAVIGATION OR EMERGENCY
# ============================================================

@router.post(
    "/navigate",
    response_model=VoiceNavigationResponse,
)
def voice_navigation(

    payload: VoiceNavigationRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

    notifier: NotificationService = Depends(
        get_notification_service
    ),
):

    command = speech_service.parse_command(
        payload.text
    )


    # --------------------------------------------------------
    # EMERGENCY COMMAND
    # --------------------------------------------------------

    if command["intent"] == "EMERGENCY":

        event = trigger_voice_emergency(
            db=db,
            current_user=current_user,
            notifier=notifier,
            latitude=payload.origin_latitude,
            longitude=payload.origin_longitude,
        )

        return VoiceNavigationResponse(

            recognized_text=command[
                "recognized_text"
            ],

            intent="EMERGENCY",

            destination=None,

            command_response=(
                f"Emergency alert activated. "
                f"Emergency ID {event.id}."
            ),

            navigation_started=False,
        )


    # --------------------------------------------------------
    # NOT A NAVIGATION COMMAND
    # --------------------------------------------------------

    if command["intent"] != "NAVIGATE":

        return VoiceNavigationResponse(

            recognized_text=command[
                "recognized_text"
            ],

            intent=command["intent"],

            destination=command[
                "destination"
            ],

            command_response=command[
                "response"
            ],

            navigation_started=False,
        )


    # --------------------------------------------------------
    # CREATE REAL WALKING ROUTE
    # --------------------------------------------------------

    destination = command["destination"]


    try:

        route = navigation_service.create_real_route(

            destination=destination,

            origin_lat=payload.origin_latitude,

            origin_lng=payload.origin_longitude,

            destination_lat=(
                payload.destination_latitude
            ),

            destination_lng=(
                payload.destination_longitude
            ),
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


    except RuntimeError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )


    first_step = route["steps"][0]


    return VoiceNavigationResponse(

        recognized_text=command[
            "recognized_text"
        ],

        intent="NAVIGATE",

        destination=destination,

        command_response=(
            f"Starting real walking navigation "
            f"to {destination}."
        ),

        navigation_started=True,

        route_id=route["route_id"],

        total_distance_m=route[
            "total_distance_m"
        ],

        estimated_time_minutes=route[
            "estimated_time_minutes"
        ],

        navigation_status=route[
            "navigation_status"
        ],

        current_instruction=route[
            "current_instruction"
        ],

        voice_instruction=(
            first_step.voice_instruction
        ),

        steps=route["steps"],
    )


# ============================================================
# 3. AUDIO → WHISPER → COMMAND OR EMERGENCY
# ============================================================

@router.post(
    "/audio",
    response_model=AudioCommandResponse,
)
def process_audio_command(

    audio: UploadFile = File(...),

    latitude: float | None = None,

    longitude: float | None = None,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

    notifier: NotificationService = Depends(
        get_notification_service
    ),
):

    temp_path = None


    try:

        temp_path = save_temp_audio(
            audio
        )


        transcription = whisper_service.transcribe(
            temp_path
        )


        if not transcription["text"]:

            raise HTTPException(
                status_code=400,
                detail="No speech detected in audio.",
            )


        command = speech_service.parse_command(
            transcription["text"]
        )


        # ----------------------------------------------------
        # AUDIO EMERGENCY
        # ----------------------------------------------------

        if command["intent"] == "EMERGENCY":

            event = trigger_voice_emergency(

                db=db,

                current_user=current_user,

                notifier=notifier,

                latitude=latitude,

                longitude=longitude,
            )


            command["response"] = (

                f"Emergency alert activated. "
                f"Emergency ID {event.id}."
            )


        return AudioCommandResponse(

            transcription=transcription[
                "text"
            ],

            detected_language=transcription[
                "language"
            ],

            language_probability=transcription[
                "language_probability"
            ],

            intent=command["intent"],

            destination=command[
                "destination"
            ],

            command_response=command[
                "response"
            ],
        )


    finally:

        try:

            audio.file.close()

        except Exception:

            pass


        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            os.remove(temp_path)


# ============================================================
# 4. AUDIO → WHISPER → REAL NAVIGATION OR EMERGENCY
# ============================================================

@router.post(
    "/audio/navigate",
    response_model=AudioNavigationResponse,
)
def audio_navigation(

    audio: UploadFile = File(...),

    origin_latitude: float | None = None,

    origin_longitude: float | None = None,

    destination_latitude: float | None = None,

    destination_longitude: float | None = None,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

    notifier: NotificationService = Depends(
        get_notification_service
    ),
):

    temp_path = None


    try:

        temp_path = save_temp_audio(
            audio
        )


        # ----------------------------------------------------
        # WHISPER TRANSCRIPTION
        # ----------------------------------------------------

        transcription = whisper_service.transcribe(
            temp_path
        )


        if not transcription["text"]:

            raise HTTPException(
                status_code=400,
                detail="No speech detected in audio.",
            )


        # ----------------------------------------------------
        # COMMAND PARSING
        # ----------------------------------------------------

        command = speech_service.parse_command(
            transcription["text"]
        )


        # ----------------------------------------------------
        # AUDIO EMERGENCY
        # ----------------------------------------------------

        if command["intent"] == "EMERGENCY":

            event = trigger_voice_emergency(

                db=db,

                current_user=current_user,

                notifier=notifier,

                latitude=origin_latitude,

                longitude=origin_longitude,
            )


            return AudioNavigationResponse(

                transcription=transcription[
                    "text"
                ],

                detected_language=transcription[
                    "language"
                ],

                language_probability=transcription[
                    "language_probability"
                ],

                intent="EMERGENCY",

                destination=None,

                command_response=(
                    f"Emergency alert activated. "
                    f"Emergency ID {event.id}."
                ),

                navigation_started=False,
            )


        # ----------------------------------------------------
        # NOT NAVIGATION
        # ----------------------------------------------------

        if command["intent"] != "NAVIGATE":

            return AudioNavigationResponse(

                transcription=transcription[
                    "text"
                ],

                detected_language=transcription[
                    "language"
                ],

                language_probability=transcription[
                    "language_probability"
                ],

                intent=command["intent"],

                destination=command[
                    "destination"
                ],

                command_response=command[
                    "response"
                ],

                navigation_started=False,
            )


        # ----------------------------------------------------
        # CREATE REAL WALKING ROUTE
        # ----------------------------------------------------

        destination = command["destination"]


        try:

            route = navigation_service.create_real_route(

                destination=destination,

                origin_lat=origin_latitude,

                origin_lng=origin_longitude,

                destination_lat=(
                    destination_latitude
                ),

                destination_lng=(
                    destination_longitude
                ),
            )


        except ValueError as exc:

            raise HTTPException(
                status_code=400,
                detail=str(exc),
            )


        except RuntimeError as exc:

            raise HTTPException(
                status_code=502,
                detail=str(exc),
            )


        first_step = route["steps"][0]


        return AudioNavigationResponse(

            transcription=transcription[
                "text"
            ],

            detected_language=transcription[
                "language"
            ],

            language_probability=transcription[
                "language_probability"
            ],

            intent="NAVIGATE",

            destination=destination,

            command_response=(
                f"Starting real walking navigation "
                f"to {destination}."
            ),

            navigation_started=True,

            route_id=route[
                "route_id"
            ],

            total_distance_m=route[
                "total_distance_m"
            ],

            estimated_time_minutes=route[
                "estimated_time_minutes"
            ],

            navigation_status=route[
                "navigation_status"
            ],

            current_instruction=route[
                "current_instruction"
            ],

            voice_instruction=(
                first_step.voice_instruction
            ),

            steps=route["steps"],
        )


    finally:

        try:

            audio.file.close()

        except Exception:

            pass


        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            os.remove(temp_path)