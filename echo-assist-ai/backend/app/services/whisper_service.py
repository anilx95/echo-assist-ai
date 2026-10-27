
import os

from faster_whisper import WhisperModel


class WhisperService:

    def __init__(self):

        model_name = os.getenv(
            "WHISPER_MODEL",
            "tiny",
        )

        device = os.getenv(
            "WHISPER_DEVICE",
            "cpu",
        )

        compute_type = os.getenv(
            "WHISPER_COMPUTE_TYPE",
            "int8",
        )

        print(
            f"Loading Whisper model: {model_name}..."
        )

        self.model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )

        print(
            f"Whisper {model_name} ready on {device}"
        )


    def transcribe(
        self,
        audio_path: str,
    ):

        segments, info = self.model.transcribe(

            audio_path,

            # Current voice-command parser expects English commands
            language="en",

            task="transcribe",

            # Better accuracy than beam_size=1
            beam_size=5,

            best_of=5,

            # Remove silence and non-speech sections
            vad_filter=True,

            vad_parameters={
                "min_silence_duration_ms": 500,
            },

            # Prevent previous incorrect text from affecting
            # the next segment
            condition_on_previous_text=False,

            # Give the model context about expected commands
            initial_prompt=(
                "ECHO-ASSIST AI smart cane voice assistant. "
                "The user gives navigation and emergency commands. "
                "Example commands: "
                "Take me to college. "
                "Take me home. "
                "Navigate to hospital. "
                "Go to the bus stop. "
                "Directions to railway station. "
                "Stop navigation. "
                "Cancel navigation. "
                "Repeat instruction. "
                "Say again. "
                "Help me. "
                "Emergency. "
                "Call emergency contact."
            ),
        )


        text_parts = []


        for segment in segments:

            cleaned_text = (
                segment.text
                .strip()
            )

            if cleaned_text:

                text_parts.append(
                    cleaned_text
                )


        final_text = " ".join(
            text_parts
        ).strip()


        return {

            "text": final_text,

            "language": info.language,

            "language_probability": round(
                float(
                    info.language_probability
                ),
                4,
            ),
        }


whisper_service = WhisperService()