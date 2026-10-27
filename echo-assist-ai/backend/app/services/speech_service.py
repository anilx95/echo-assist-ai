import re


class SpeechService:

    def parse_command(self, text: str):

        original_text = text.strip()

        normalized = original_text.lower().strip()

        navigation_patterns = [
            r"take me to (.+)",
            r"navigate to (.+)",
            r"go to (.+)",
            r"directions to (.+)",
            r"route to (.+)",
        ]

        for pattern in navigation_patterns:

            match = re.search(
                pattern,
                normalized,
            )

            if match:

                destination = (
                    match.group(1)
                    .strip()
                    .rstrip(".")
                )

                return {
                    "recognized_text": original_text,
                    "intent": "NAVIGATE",
                    "destination": destination,
                    "confidence": 1.0,
                    "response": (
                        f"Starting navigation to "
                        f"{destination}."
                    ),
                }


        emergency_words = [
            "help me",
            "emergency",
            "sos",
            "call emergency contact",
        ]

        for phrase in emergency_words:

            if phrase in normalized:

                return {
                    "recognized_text": original_text,
                    "intent": "EMERGENCY",
                    "destination": None,
                    "confidence": 1.0,
                    "response": (
                        "Emergency command detected."
                    ),
                }


        stop_navigation_patterns = [
            "stop navigation",
            "cancel navigation",
            "end navigation",
        ]

        for phrase in stop_navigation_patterns:

            if phrase in normalized:

                return {
                    "recognized_text": original_text,
                    "intent": "STOP_NAVIGATION",
                    "destination": None,
                    "confidence": 1.0,
                    "response": (
                        "Navigation stopped."
                    ),
                }


        repeat_patterns = [
            "repeat instruction",
            "repeat direction",
            "say again",
            "repeat",
        ]

        for phrase in repeat_patterns:

            if phrase in normalized:

                return {
                    "recognized_text": original_text,
                    "intent": "REPEAT_INSTRUCTION",
                    "destination": None,
                    "confidence": 1.0,
                    "response": (
                        "Repeating the current instruction."
                    ),
                }


        return {
            "recognized_text": original_text,
            "intent": "UNKNOWN",
            "destination": None,
            "confidence": 0.0,
            "response": (
                "Sorry, I could not understand the command."
            ),
        }


speech_service = SpeechService()