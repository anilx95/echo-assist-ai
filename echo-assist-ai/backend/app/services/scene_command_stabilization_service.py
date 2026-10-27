from collections import deque
from copy import deepcopy
from typing import Any, Deque, Dict, Optional


class SceneCommandStabilizationService:
    """
    Stabilizes frame-by-frame scene commands before they are
    sent to the smart cane output controller.

    Safety behaviour:
    - STOP is applied immediately.
    - EMERGENCY_STOP is applied immediately.
    - Direction changes require confirmation.
    - MOVE_LEFT <-> MOVE_RIGHT oscillation is prevented.
    - Lower-risk actions are released gradually.
    - Initial safe commands can be accepted immediately.
    """

    DIRECTION_ACTIONS = {
        "MOVE_LEFT",
        "MOVE_RIGHT",
    }

    IMMEDIATE_ACTIONS = {
        "STOP",
        "EMERGENCY_STOP",
    }

    VALID_ACTIONS = {
        "CONTINUE",
        "SLOW_DOWN",
        "CAUTION",
        "MOVE_LEFT",
        "MOVE_RIGHT",
        "STOP",
        "EMERGENCY_STOP",
    }

    ACTION_SEVERITY = {
        "CONTINUE": 0,
        "SLOW_DOWN": 1,
        "CAUTION": 2,
        "MOVE_LEFT": 3,
        "MOVE_RIGHT": 3,
        "STOP": 4,
        "EMERGENCY_STOP": 5,
    }

    def __init__(
        self,
        direction_confirmation_frames: int = 2,
        release_confirmation_frames: int = 2,
        history_size: int = 5,
    ):

        self.direction_confirmation_frames = max(
            1,
            direction_confirmation_frames,
        )

        self.release_confirmation_frames = max(
            1,
            release_confirmation_frames,
        )

        self.action_history: Deque[str] = deque(
            maxlen=max(3, history_size)
        )

        self.current_stable_decision: Optional[
            Dict[str, Any]
        ] = None

        self.pending_action: Optional[str] = None

        self.pending_count: int = 0

        self.frame_number: int = 0


    # ============================================================
    # MAIN STABILIZATION METHOD
    # ============================================================

    def stabilize(
        self,
        scene_decision: Dict[str, Any],
    ) -> Dict[str, Any]:

        self.frame_number += 1

        if not scene_decision:
            return self._force_safe_stop(
                reason="Scene decision was empty."
            )

        raw_decision = deepcopy(scene_decision)

        raw_action = str(
            raw_decision.get(
                "action",
                "STOP",
            )
        ).upper()

        if raw_action not in self.VALID_ACTIONS:
            return self._force_safe_stop(
                reason=(
                    f"Invalid scene action received: "
                    f"{raw_action}"
                )
            )

        self.action_history.append(
            raw_action
        )

        # ========================================================
        # RULE 1: STOP AND EMERGENCY STOP ARE IMMEDIATE
        # ========================================================

        if raw_action in self.IMMEDIATE_ACTIONS:

            self.current_stable_decision = deepcopy(
                raw_decision
            )

            self.pending_action = None
            self.pending_count = 0

            return self._build_result(
                raw_decision=raw_decision,
                stable_decision=raw_decision,
                status="IMMEDIATE_SAFETY_OVERRIDE",
                confirmation_count=1,
                confirmation_required=1,
            )

        # ========================================================
        # RULE 2: FIRST NON-DANGER DECISION
        # ========================================================

        if self.current_stable_decision is None:

            self.current_stable_decision = deepcopy(
                raw_decision
            )

            self.pending_action = None
            self.pending_count = 0

            return self._build_result(
                raw_decision=raw_decision,
                stable_decision=raw_decision,
                status="INITIALIZED",
                confirmation_count=1,
                confirmation_required=1,
            )

        stable_action = str(
            self.current_stable_decision.get(
                "action",
                "STOP",
            )
        ).upper()

        # ========================================================
        # RULE 3: SAME ACTION CONTINUES
        # ========================================================

        if raw_action == stable_action:

            self.current_stable_decision = deepcopy(
                raw_decision
            )

            self.pending_action = None
            self.pending_count = 0

            return self._build_result(
                raw_decision=raw_decision,
                stable_decision=raw_decision,
                status="STABLE",
                confirmation_count=0,
                confirmation_required=0,
            )

        # ========================================================
        # RULE 4: DETERMINE REQUIRED CONFIRMATION
        # ========================================================

        confirmation_required = (
            self._confirmation_required(
                current_action=stable_action,
                new_action=raw_action,
            )
        )

        # ========================================================
        # RULE 5: UPDATE PENDING ACTION
        # ========================================================

        if self.pending_action == raw_action:

            self.pending_count += 1

        else:

            self.pending_action = raw_action
            self.pending_count = 1

        # ========================================================
        # RULE 6: CONFIRM ACTION CHANGE
        # ========================================================

        if (
            self.pending_count
            >= confirmation_required
        ):

            self.current_stable_decision = deepcopy(
                raw_decision
            )

            confirmed_count = self.pending_count

            self.pending_action = None
            self.pending_count = 0

            return self._build_result(
                raw_decision=raw_decision,
                stable_decision=raw_decision,
                status="ACTION_CHANGE_CONFIRMED",
                confirmation_count=confirmed_count,
                confirmation_required=(
                    confirmation_required
                ),
            )

        # ========================================================
        # RULE 7: HOLD PREVIOUS STABLE ACTION
        # ========================================================

        held_decision = deepcopy(
            self.current_stable_decision
        )

        return self._build_result(
            raw_decision=raw_decision,
            stable_decision=held_decision,
            status="HOLDING_PREVIOUS_ACTION",
            confirmation_count=self.pending_count,
            confirmation_required=(
                confirmation_required
            ),
        )


    # ============================================================
    # CONFIRMATION POLICY
    # ============================================================

    def _confirmation_required(
        self,
        current_action: str,
        new_action: str,
    ) -> int:

        # Direction changes need confirmation.

        if new_action in self.DIRECTION_ACTIONS:
            return self.direction_confirmation_frames

        # Releasing from STOP requires stable safer evidence.

        if current_action in self.IMMEDIATE_ACTIONS:
            return self.release_confirmation_frames

        current_severity = self.ACTION_SEVERITY.get(
            current_action,
            4,
        )

        new_severity = self.ACTION_SEVERITY.get(
            new_action,
            4,
        )

        # Escalation is accepted immediately except direction
        # commands, which were handled above.

        if new_severity > current_severity:
            return 1

        # De-escalation requires confirmation.

        if new_severity < current_severity:
            return self.release_confirmation_frames

        return 1


    # ============================================================
    # RESULT BUILDER
    # ============================================================

    def _build_result(
        self,
        raw_decision: Dict[str, Any],
        stable_decision: Dict[str, Any],
        status: str,
        confirmation_count: int,
        confirmation_required: int,
    ) -> Dict[str, Any]:

        result = deepcopy(
            stable_decision
        )

        raw_action = str(
            raw_decision.get(
                "action",
                "STOP",
            )
        ).upper()

        stable_action = str(
            stable_decision.get(
                "action",
                "STOP",
            )
        ).upper()

        result[
            "command_stabilization"
        ] = {
            "raw_action": raw_action,
            "stable_action": stable_action,
            "action_changed": (
                raw_action != stable_action
            ),
            "status": status,
            "pending_action": self.pending_action,
            "confirmation_count": (
                confirmation_count
            ),
            "confirmation_required": (
                confirmation_required
            ),
            "frame_number": self.frame_number,
            "action_history": list(
                self.action_history
            ),
        }

        return result


    # ============================================================
    # FAIL-SAFE STOP
    # ============================================================

    def _force_safe_stop(
        self,
        reason: str,
    ) -> Dict[str, Any]:

        safe_decision = {
            "action": "STOP",
            "voice_message": (
                "System safety warning. "
                "Please stop and wait."
            ),
            "vibration": "STRONG_CONTINUOUS",
            "priority": 1,
            "reason": reason,
        }

        self.current_stable_decision = deepcopy(
            safe_decision
        )

        self.pending_action = None
        self.pending_count = 0

        return self._build_result(
            raw_decision=safe_decision,
            stable_decision=safe_decision,
            status="FAIL_SAFE_STOP",
            confirmation_count=1,
            confirmation_required=1,
        )


    # ============================================================
    # RESET
    # ============================================================

    def reset(self) -> None:

        self.action_history.clear()

        self.current_stable_decision = None

        self.pending_action = None

        self.pending_count = 0

        self.frame_number = 0


scene_command_stabilization_service = (
    SceneCommandStabilizationService()
)