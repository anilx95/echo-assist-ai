import time


class NavigationCommandService:

    # ==========================================================
    # BUILD FINAL NAVIGATION COMMAND
    # ==========================================================

    def build_command(
        self,
        scene_decision: dict,
        stabilized_scene_decision: dict,
        cane_output: dict,
        primary_warning: dict | None,
    ):

        # ---------------------------------------------
        # FINAL ACTION
        # ---------------------------------------------

        action = (
            stabilized_scene_decision.get(
                "action"
            )
            or scene_decision.get(
                "action",
                "UNKNOWN",
            )
        )

        priority = (
            stabilized_scene_decision.get(
                "priority"
            )
            or scene_decision.get(
                "priority",
                0,
            )
        )

        # ---------------------------------------------
        # VOICE
        # ---------------------------------------------

        voice = (
            cane_output.get(
                "voice_output",
                {},
            ).get(
                "message",
                "",
            )
        )

        # ---------------------------------------------
        # OBJECT INFORMATION
        # ---------------------------------------------

        object_info = {

            "name": None,

            "distance_cm": None,

            "direction": None,

            "risk": None,
        }

        if primary_warning:

            detection = (
                primary_warning.get(
                    "detection",
                    {},
                )
            )

            distance = (
                primary_warning.get(
                    "distance_estimation",
                    {},
                )
            )

            risk = (
                primary_warning.get(
                    "risk_prediction",
                    {},
                )
            )

            object_info = {

                "name":
                    detection.get(
                        "object_type"
                    ),

                "distance_cm":
                    distance.get(
                        "estimated_distance_cm"
                    ),

                "direction":
                    detection.get(
                        "direction"
                    ),

                "risk":
                    risk.get(
                        "risk_level"
                    ),
            }

        # ---------------------------------------------
        # HARDWARE
        # ---------------------------------------------

        hardware = {}

        commands = (
            cane_output.get(
                "hardware_commands",
                {}
            )
        )

        hardware["left_vibration"] = (
            commands.get(
                "left_vibration",
                {},
            ).get(
                "pattern"
            )
        )

        hardware["right_vibration"] = (
            commands.get(
                "right_vibration",
                {},
            ).get(
                "pattern"
            )
        )

        hardware["main_vibration"] = (
            commands.get(
                "main_vibration",
                {},
            ).get(
                "pattern"
            )
        )

        hardware["buzzer"] = (
            commands.get(
                "buzzer",
                {},
            ).get(
                "pattern"
            )
        )

        # ---------------------------------------------
        # AUDIO
        # ---------------------------------------------

        audio = {

            "tts": True,

            "repeat": True,

            "language": "en",
        }

        # ---------------------------------------------
        # FINAL COMMAND
        # ---------------------------------------------

        return {

            "action": action,

            "priority": priority,

            "voice": voice,

            "object": object_info,

            "hardware": hardware,

            "audio": audio,

            "timestamp": time.time(),
        }


navigation_command_service = (
    NavigationCommandService()
)