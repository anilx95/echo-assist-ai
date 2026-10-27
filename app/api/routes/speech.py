from app.schemas.speech import (
    AudioCommandResponse,
    AudioNavigationResponse,
    VoiceCommandRequest,
    VoiceCommandResponse,
    VoiceNavigationRequest,
    VoiceNavigationResponse,
)
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
):

    allowed_extensions = {
        ".wav",
        ".mp3",
        ".m4a",
        ".ogg",
        ".webm",
    }

    original_filename = (
        audio.filename or "audio.wav"
    )

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. "
                "Use WAV, MP3, M4A, OGG, or WEBM."
            ),
        )

    temp_path = None

    try:

        # ------------------------------------------
        # SAVE TEMPORARY AUDIO
        # ------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            shutil.copyfileobj(
                audio.file,
                temp_file,
            )

            temp_path = temp_file.name


        # ------------------------------------------
        # WHISPER TRANSCRIPTION
        # ------------------------------------------

        transcription = (
            whisper_service.transcribe(
                temp_path
            )
        )


        if not transcription["text"]:

            raise HTTPException(
                status_code=400,
                detail="No speech detected in audio.",
            )


        # ------------------------------------------
        # COMMAND UNDERSTANDING
        # ------------------------------------------

        command = (
            speech_service.parse_command(
                transcription["text"]
            )
        )


        # ------------------------------------------
        # NON-NAVIGATION COMMAND
        # ------------------------------------------

        if command["intent"] != "NAVIGATE":

            return AudioNavigationResponse(

                transcription=(
                    transcription["text"]
                ),

                detected_language=(
                    transcription["language"]
                ),

                language_probability=(
                    transcription[
                        "language_probability"
                    ]
                ),

                intent=command["intent"],

                destination=(
                    command["destination"]
                ),

                command_response=(
                    command["response"]
                ),

                navigation_started=False,
            )


        # ------------------------------------------
        # DESTINATION
        # ------------------------------------------

        destination = command[
            "destination"
        ]


        # ------------------------------------------
        # CREATE NAVIGATION ROUTE
        # ------------------------------------------

        route = (
            navigation_service.create_mock_route(

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
        )


        first_step = route["steps"][0]


        # ------------------------------------------
        # COMPLETE RESPONSE
        # ------------------------------------------

        return AudioNavigationResponse(

            transcription=(
                transcription["text"]
            ),

            detected_language=(
                transcription["language"]
            ),

            language_probability=(
                transcription[
                    "language_probability"
                ]
            ),

            intent="NAVIGATE",

            destination=destination,

            command_response=(
                f"Starting navigation to "
                f"{destination}."
            ),

            navigation_started=True,

            route_id=route["route_id"],

            total_distance_m=(
                route["total_distance_m"]
            ),

            estimated_time_minutes=(
                route[
                    "estimated_time_minutes"
                ]
            ),

            navigation_status=(
                route["navigation_status"]
            ),

            current_instruction=(
                route["current_instruction"]
            ),

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