from typing import Any, Dict, Optional


class CaneOutputService:
    """
    Converts the final AI scene decision into hardware-friendly
    commands for the smart cane.

    Current prototype outputs:
    - left vibration motor
    - right vibration motor
    - main vibration motor
    - buzzer
    - voice message

    Later these commands can be sent to ESP32 through:
    - HTTP
    - WebSocket
    - Bluetooth
    - Serial communication
    """


    VALID_ACTIONS = {
        "CONTINUE",
        "SLOW_DOWN",
        "CAUTION",
        "MOVE_LEFT",
        "MOVE_RIGHT",
        "STOP",
        "EMERGENCY_STOP",
    }


    def __init__(self):

        self.last_command: Optional[Dict[str, Any]] = None

        print("Cane Output Controller ready.")


    # ============================================================
    # MAIN OUTPUT GENERATOR
    # ============================================================

    def generate_output(
        self,
        scene_decision: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not scene_decision:

            command = self._safe_stop_command(
                reason="Scene decision was empty."
            )

            self.last_command = command

            return command


        action = str(
            scene_decision.get(
                "action",
                "STOP",
            )
        ).upper()


        voice_message = scene_decision.get(
            "voice_message",
            "Please stop and wait.",
        )


        priority = int(
            scene_decision.get(
                "priority",
                1,
            )
        )


        reason = scene_decision.get(
            "reason",
            "No reason provided.",
        )


        if action not in self.VALID_ACTIONS:

            command = self._safe_stop_command(
                reason=(
                    f"Unknown scene action received: {action}"
                )
            )

            self.last_command = command

            return command


        if action == "CONTINUE":

            command = self._continue_command(
                voice_message=voice_message,
                priority=priority,
                reason=reason,
            )


        elif action in {
            "SLOW_DOWN",
            "CAUTION",
        }:

            command = self._caution_command(
                action=action,
                voice_message=voice_message,
                priority=priority,
                reason=reason,
            )


        elif action == "MOVE_LEFT":

            command = self._move_left_command(
                voice_message=voice_message,
                priority=priority,
                reason=reason,
            )


        elif action == "MOVE_RIGHT":

            command = self._move_right_command(
                voice_message=voice_message,
                priority=priority,
                reason=reason,
            )


        elif action == "STOP":

            command = self._stop_command(
                voice_message=voice_message,
                priority=priority,
                reason=reason,
            )


        elif action == "EMERGENCY_STOP":

            command = self._emergency_stop_command(
                voice_message=voice_message,
                priority=priority,
                reason=reason,
            )


        else:

            command = self._safe_stop_command(
                reason="Unhandled action."
            )


        self.last_command = command

        return command


    # ============================================================
    # CONTINUE
    # ============================================================

    def _continue_command(
        self,
        voice_message: str,
        priority: int,
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "controller_status": "READY",

            "action": "CONTINUE",

            "hardware_commands": {
                "left_vibration": {
                    "enabled": False,
                    "intensity": 0,
                    "pattern": "OFF",
                },

                "right_vibration": {
                    "enabled": False,
                    "intensity": 0,
                    "pattern": "OFF",
                },

                "main_vibration": {
                    "enabled": False,
                    "intensity": 0,
                    "pattern": "OFF",
                },

                "buzzer": {
                    "enabled": False,
                    "pattern": "OFF",
                },
            },

            "voice_output": {
                "enabled": True,
                "message": voice_message,
            },

            "priority": priority,

            "reason": reason,
        }


    # ============================================================
    # CAUTION / SLOW DOWN
    # ============================================================

    def _caution_command(
        self,
        action: str,
        voice_message: str,
        priority: int,
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "controller_status": "READY",

            "action": action,

            "hardware_commands": {
                "left_vibration": {
                    "enabled": False,
                    "intensity": 0,
                    "pattern": "OFF",
                },

                "right_vibration": {
                    "enabled": False,
                    "intensity": 0,
                    "pattern": "OFF",
                },

                "main_vibration": {
                    "enabled": True,
                    "intensity": 35,
                    "pattern": "SHORT_PULSE",
                },

                "buzzer": {
                    "enabled": False,
                    "pattern": "OFF",
                },
            },

            "voice_output": {
                "enabled": True,
                "message": voice_message,
            },

            "priority": priority,

            "reason": reason,
        }


    # ============================================================
    # MOVE LEFT
    # ============================================================

    def _move_left_command(
        self,
        voice_message: str,
        priority: int,
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "controller_status": "READY",

            "action": "MOVE_LEFT",

            "hardware_commands": {
                "left_vibration": {
                    "enabled": True,
                    "intensity": 65,
                    "pattern": "DIRECTION_PULSE",
                },

                "right_vibration": {
                    "enabled": False,
                    "intensity": 0,
                    "pattern": "OFF",
                },

                "main_vibration": {
                    "enabled": False,
                    "intensity": 0,
                    "pattern": "OFF",
                },

                "buzzer": {
                    "enabled": False,
                    "pattern": "OFF",
                },
            },

            "voice_output": {
                "enabled": True,
                "message": voice_message,
            },

            "priority": priority,

            "reason": reason,
        }


    # ============================================================
    # MOVE RIGHT
    # ============================================================

    def _move_right_command(
        self,
        voice_message: str,
        priority: int,
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "controller_status": "READY",

            "action": "MOVE_RIGHT",

            "hardware_commands": {
                "left_vibration": {
                    "enabled": False,
                    "intensity": 0,
                    "pattern": "OFF",
                },

                "right_vibration": {
                    "enabled": True,
                    "intensity": 65,
                    "pattern": "DIRECTION_PULSE",
                },

                "main_vibration": {
                    "enabled": False,
                    "intensity": 0,
                    "pattern": "OFF",
                },

                "buzzer": {
                    "enabled": False,
                    "pattern": "OFF",
                },
            },

            "voice_output": {
                "enabled": True,
                "message": voice_message,
            },

            "priority": priority,

            "reason": reason,
        }


    # ============================================================
    # STOP
    # ============================================================

    def _stop_command(
        self,
        voice_message: str,
        priority: int,
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "controller_status": "READY",

            "action": "STOP",

            "hardware_commands": {
                "left_vibration": {
                    "enabled": True,
                    "intensity": 100,
                    "pattern": "CONTINUOUS",
                },

                "right_vibration": {
                    "enabled": True,
                    "intensity": 100,
                    "pattern": "CONTINUOUS",
                },

                "main_vibration": {
                    "enabled": True,
                    "intensity": 100,
                    "pattern": "CONTINUOUS",
                },

                "buzzer": {
                    "enabled": True,
                    "pattern": "WARNING_BEEP",
                },
            },

            "voice_output": {
                "enabled": True,
                "message": voice_message,
            },

            "priority": priority,

            "reason": reason,
        }


    # ============================================================
    # EMERGENCY STOP
    # ============================================================

    def _emergency_stop_command(
        self,
        voice_message: str,
        priority: int,
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "controller_status": "EMERGENCY",

            "action": "EMERGENCY_STOP",

            "hardware_commands": {
                "left_vibration": {
                    "enabled": True,
                    "intensity": 100,
                    "pattern": "RAPID_PULSE",
                },

                "right_vibration": {
                    "enabled": True,
                    "intensity": 100,
                    "pattern": "RAPID_PULSE",
                },

                "main_vibration": {
                    "enabled": True,
                    "intensity": 100,
                    "pattern": "RAPID_PULSE",
                },

                "buzzer": {
                    "enabled": True,
                    "pattern": "EMERGENCY_ALARM",
                },
            },

            "voice_output": {
                "enabled": True,
                "message": voice_message,
            },

            "priority": priority,

            "reason": reason,
        }


    # ============================================================
    # FAIL-SAFE
    # ============================================================

    def _safe_stop_command(
        self,
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "controller_status": "FAIL_SAFE",

            "action": "STOP",

            "hardware_commands": {
                "left_vibration": {
                    "enabled": True,
                    "intensity": 100,
                    "pattern": "CONTINUOUS",
                },

                "right_vibration": {
                    "enabled": True,
                    "intensity": 100,
                    "pattern": "CONTINUOUS",
                },

                "main_vibration": {
                    "enabled": True,
                    "intensity": 100,
                    "pattern": "CONTINUOUS",
                },

                "buzzer": {
                    "enabled": True,
                    "pattern": "WARNING_BEEP",
                },
            },

            "voice_output": {
                "enabled": True,
                "message": (
                    "System safety warning. "
                    "Please stop and wait."
                ),
            },

            "priority": 1,

            "reason": reason,
        }


    # ============================================================
    # LAST COMMAND
    # ============================================================

    def get_last_command(
        self,
    ) -> Optional[Dict[str, Any]]:

        return self.last_command


cane_output_service = CaneOutputService()