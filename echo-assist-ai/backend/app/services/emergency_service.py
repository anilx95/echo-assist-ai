from sqlalchemy.orm import Session

from app.models.contact import EmergencyContact
from app.models.emergency_event import EmergencyEvent
from app.models.notification import Notification
from app.models.user import User
from app.services.notification_service import NotificationService


class EmergencyService:

    def create_pending_emergency(
        self,
        db: Session,
        user: User,
        event_type: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> EmergencyEvent:

        existing_event = (
            db.query(EmergencyEvent)
            .filter(
                EmergencyEvent.user_id == user.id,
                EmergencyEvent.status.in_(
                    [
                        "PENDING_CONFIRMATION",
                        "ACTIVE",
                    ]
                ),
            )
            .order_by(
                EmergencyEvent.created_at.desc()
            )
            .first()
        )

        if existing_event:
            return existing_event

        event = EmergencyEvent(
            user_id=user.id,
            event_type=event_type,
            latitude=latitude,
            longitude=longitude,
            status="PENDING_CONFIRMATION",
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event


    def trigger_emergency(
        self,
        db: Session,
        user: User,
        notifier: NotificationService,
        event_type: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> EmergencyEvent:

        existing_event = (
            db.query(EmergencyEvent)
            .filter(
                EmergencyEvent.user_id == user.id,
                EmergencyEvent.status == "ACTIVE",
            )
            .order_by(
                EmergencyEvent.created_at.desc()
            )
            .first()
        )

        if existing_event:
            return existing_event

        event = EmergencyEvent(
            user_id=user.id,
            event_type=event_type,
            latitude=latitude,
            longitude=longitude,
            status="ACTIVE",
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        self.send_emergency_notifications(
            db=db,
            user=user,
            notifier=notifier,
            event=event,
        )

        return event


    def escalate_emergency(
        self,
        db: Session,
        user: User,
        notifier: NotificationService,
        emergency_id: int,
    ) -> EmergencyEvent | None:

        event = (
            db.query(EmergencyEvent)
            .filter(
                EmergencyEvent.id == emergency_id,
                EmergencyEvent.user_id == user.id,
            )
            .first()
        )

        if not event:
            return None

        if event.status == "CANCELLED":
            return event

        if event.status == "ACTIVE":
            return event

        if event.status != "PENDING_CONFIRMATION":
            return event

        event.status = "ACTIVE"

        db.commit()
        db.refresh(event)

        self.send_emergency_notifications(
            db=db,
            user=user,
            notifier=notifier,
            event=event,
        )

        return event


    def send_emergency_notifications(
        self,
        db: Session,
        user: User,
        notifier: NotificationService,
        event: EmergencyEvent,
    ) -> None:

        contacts = (
            db.query(EmergencyContact)
            .filter(
                EmergencyContact.user_id == user.id
            )
            .all()
        )

        if (
            event.latitude is not None
            and event.longitude is not None
        ):
            location_text = (
                f"Location: "
                f"https://maps.google.com/?q="
                f"{event.latitude},{event.longitude}"
            )
        else:
            location_text = (
                "Location is currently unavailable."
            )

        message = (
            f"EMERGENCY ALERT: "
            f"{user.full_name} may need help. "
            f"Event: {event.event_type}. "
            f"{location_text}"
        )

        for contact in contacts:
            sms_delivered = notifier.send_sms(contact.phone_number, message)
            db.add(Notification(
                user_id=user.id, sos_alert_id=event.id, channel="sms", recipient=contact.phone_number,
                title="Emergency Alert", message=message,
                status="delivered" if sms_delivered else "not_delivered",
            ))

            if contact.email:
                email_delivered = notifier.send_email(contact.email, "Emergency Alert - ECHO-ASSIST AI", message)
                db.add(Notification(
                    user_id=user.id, sos_alert_id=event.id, channel="email", recipient=contact.email,
                    title="Emergency Alert", message=message,
                    status="delivered" if email_delivered else "not_delivered",
                ))

        push_delivered = notifier.send_push(user.id, "Emergency Alert", message)
        db.add(Notification(
            user_id=user.id, sos_alert_id=event.id, channel="push", recipient=None,
            title="Emergency Alert", message=message,
            status="delivered" if push_delivered else "not_delivered",
        ))
        db.commit()


emergency_service = EmergencyService()
