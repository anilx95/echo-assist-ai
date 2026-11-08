from abc import ABC, abstractmethod
import logging

import resend
from twilio.rest import Client

from app.core.config import settings


logger = logging.getLogger("echo_assist.notifications")


class NotificationService(ABC):

    @abstractmethod
    def send_sms(
        self,
        phone_number: str,
        message: str,
    ) -> bool:
        pass

    @abstractmethod
    def send_email(
        self,
        email: str,
        subject: str,
        message: str,
    ) -> bool:
        pass

    @abstractmethod
    def send_push(
        self,
        user_id: int,
        title: str,
        message: str,
    ) -> bool:
        pass


# ============================================================
# MOCK NOTIFICATION SERVICE
# ============================================================

class MockNotificationService(NotificationService):

    def send_sms(
        self,
        phone_number: str,
        message: str,
    ) -> bool:

        logger.info(
            "[MOCK SMS] to=%s message=%s",
            phone_number,
            message,
        )

        # A log-only mock has not delivered a real SMS.
        return False


    def send_email(
        self,
        email: str,
        subject: str,
        message: str,
    ) -> bool:

        logger.info(
            "[MOCK EMAIL] to=%s subject=%s (content withheld)",
            email,
            subject,
        )

        # A log-only mock has not delivered a real email.
        return False


    def send_push(
        self,
        user_id: int,
        title: str,
        message: str,
    ) -> bool:

        logger.info(
            "[MOCK PUSH] user_id=%s title=%s message=%s",
            user_id,
            title,
            message,
        )

        # A log-only mock has not delivered a real push notification.
        return False


# ============================================================
# REAL NOTIFICATION SERVICE
# ============================================================

class RealNotificationService(NotificationService):

    def __init__(self):

        self.twilio_client = None

        if (
            settings.TWILIO_ACCOUNT_SID
            and settings.TWILIO_AUTH_TOKEN
            and settings.TWILIO_PHONE_NUMBER
        ):

            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
            )


        if settings.RESEND_API_KEY:

            resend.api_key = (
                settings.RESEND_API_KEY
            )


    # ========================================================
    # SMS
    # ========================================================

    def send_sms(
        self,
        phone_number: str,
        message: str,
    ) -> bool:

        if not self.twilio_client:

            logger.warning(
                "Twilio is not configured. "
                "SMS was not sent."
            )

            return False


        try:

            result = (
                self.twilio_client.messages.create(

                    body=message,

                    from_=(
                        settings.TWILIO_PHONE_NUMBER
                    ),

                    to=phone_number,
                )
            )


            logger.info(
                "SMS sent successfully. sid=%s",
                result.sid,
            )

            return True


        except Exception:

            logger.exception(
                "Failed to send SMS to %s",
                phone_number,
            )

            return False


    # ========================================================
    # EMAIL
    # ========================================================

    def send_email(
        self,
        email: str,
        subject: str,
        message: str,
    ) -> bool:

        if (
            not settings.RESEND_API_KEY
            or not settings.RESEND_FROM_EMAIL
        ):

            logger.warning(
                "Resend is not configured. "
                "Email was not sent."
            )

            return False


        try:

            resend.Emails.send(
                {
                    "from": (
                        settings.RESEND_FROM_EMAIL
                    ),

                    "to": [email],

                    "subject": subject,

                    "html": (
                        f"<p>{message}</p>"
                    ),
                }
            )


            logger.info(
                "Email sent successfully to %s",
                email,
            )

            return True


        except Exception:

            logger.exception(
                "Failed to send email to %s",
                email,
            )

            return False


    # ========================================================
    # PUSH
    # ========================================================

    def send_push(
        self,
        user_id: int,
        title: str,
        message: str,
    ) -> bool:

        # Push provider will be added when the mobile app
        # and device-token storage are implemented.

        logger.info(
            "[PUSH PENDING] user_id=%s title=%s message=%s",
            user_id,
            title,
            message,
        )

        return False


# ============================================================
# PROVIDER SELECTION
# ============================================================

def get_notification_service() -> NotificationService:

    twilio_ready = bool(
        settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
        and settings.TWILIO_PHONE_NUMBER
    )

    resend_ready = bool(
        settings.RESEND_API_KEY
        and settings.RESEND_FROM_EMAIL
    )


    if twilio_ready or resend_ready:

        logger.info(
            "Using real notification service"
        )

        return RealNotificationService()


    logger.info(
        "Using mock notification service"
    )

    return MockNotificationService()
