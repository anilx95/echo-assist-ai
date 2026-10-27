import logging
import time

from app.database import SessionLocal
from app.models.emergency_event import EmergencyEvent
from app.models.user import User
from app.services.emergency_service import emergency_service
from app.services.notification_service import get_notification_service


logger = logging.getLogger("echo_assist.emergency_countdown")


def emergency_countdown_task(
    emergency_id: int,
    user_id: int,
    countdown_seconds: int = 30,
):
    """
    Wait for the confirmation countdown.

    If the emergency is still PENDING_CONFIRMATION
    after the countdown, escalate it automatically.
    """

    logger.info(
        "Countdown started for emergency %s",
        emergency_id,
    )

    time.sleep(countdown_seconds)

    db = SessionLocal()

    try:
        event = (
            db.query(EmergencyEvent)
            .filter(
                EmergencyEvent.id == emergency_id,
                EmergencyEvent.user_id == user_id,
            )
            .first()
        )

        if not event:
            logger.warning(
                "Emergency %s not found",
                emergency_id,
            )
            return

        if event.status == "CANCELLED":
            logger.info(
                "Emergency %s was cancelled",
                emergency_id,
            )
            return

        if event.status == "ACTIVE":
            logger.info(
                "Emergency %s is already active",
                emergency_id,
            )
            return

        if event.status != "PENDING_CONFIRMATION":
            logger.info(
                "Emergency %s has status %s",
                emergency_id,
                event.status,
            )
            return

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            logger.error(
                "User %s not found",
                user_id,
            )
            return

        notifier = get_notification_service()

        emergency_service.escalate_emergency(
            db=db,
            user=user,
            notifier=notifier,
            emergency_id=emergency_id,
        )

        logger.info(
            "Emergency %s automatically escalated",
            emergency_id,
        )

    except Exception:
        logger.exception(
            "Automatic escalation failed for emergency %s",
            emergency_id,
        )

    finally:
        db.close()