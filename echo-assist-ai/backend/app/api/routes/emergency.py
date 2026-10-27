from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.models.device import Device
from app.models.emergency_event import EmergencyEvent
from app.models.sensor_reading import SensorReading
from app.models.user import User

from app.schemas.emergency import (
    EmergencyCancelRequest,
    EmergencyEventResponse,
    EmergencyTriggerRequest,
    FallDetectionResponse,
)

from app.services.auth_service import get_current_user
from app.services.emergency_service import emergency_service
from app.services.fall_detection_service import (
    fall_detection_service,
)

from app.services.notification_service import (
    NotificationService,
    get_notification_service,
)


router = APIRouter(
    prefix="/emergency",
    tags=["emergency"],
)


# ============================================================
# MANUAL EMERGENCY TRIGGER WITH OPTIONAL GPS
# ============================================================

@router.post(
    "/trigger",
    response_model=EmergencyEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def trigger_emergency(
    payload: EmergencyTriggerRequest,

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

    event = emergency_service.trigger_emergency(
        db=db,
        user=current_user,
        notifier=notifier,
        event_type=payload.event_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    return event


# ============================================================
# CANCEL EMERGENCY
# ============================================================

@router.post(
    "/cancel",
    response_model=EmergencyEventResponse,
)
def cancel_emergency(
    payload: EmergencyCancelRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    event = db.get(
        EmergencyEvent,
        payload.emergency_id,
    )

    if (
        not event
        or event.user_id != current_user.id
    ):

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency not found",
        )


    event.status = "CANCELLED"

    event.resolved_at = datetime.now(
        timezone.utc
    )


    db.commit()

    db.refresh(event)


    return event


# ============================================================
# EMERGENCY HISTORY
# ============================================================

@router.get(
    "/history",
    response_model=list[EmergencyEventResponse],
)
def emergency_history(

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    return (

        db.query(EmergencyEvent)

        .filter(
            EmergencyEvent.user_id
            == current_user.id
        )

        .order_by(
            EmergencyEvent.created_at.desc()
        )

        .all()
    )


# ============================================================
# CHECK LATEST SENSOR READING FOR FALL
# ============================================================

@router.post(
    "/fall/check",
    response_model=FallDetectionResponse,
)
def check_latest_sensor_for_fall(

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

    # --------------------------------------------------------
    # GET LATEST SENSOR READING
    # --------------------------------------------------------

    reading = (

        db.query(SensorReading)

        .join(
            Device,
            Device.id == SensorReading.device_id,
        )

        .filter(
            Device.user_id == current_user.id
        )

        .order_by(
            SensorReading.received_at.desc()
        )

        .first()
    )


    if not reading:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sensor data available",
        )


    # --------------------------------------------------------
    # ANALYZE SENSOR READING
    # --------------------------------------------------------

    analysis = fall_detection_service.analyze(

        accel_x=reading.accel_x,
        accel_y=reading.accel_y,
        accel_z=reading.accel_z,

        gyro_x=reading.gyro_x,
        gyro_y=reading.gyro_y,
        gyro_z=reading.gyro_z,

        sos_pressed=reading.sos_pressed,
    )


    emergency_created = False
    emergency_id = None


    # --------------------------------------------------------
    # EMERGENCY DETECTED
    # --------------------------------------------------------

    if analysis["emergency_detected"]:

        event_type = analysis["event_type"]


        # Physical SOS is deliberate,
        # so activate immediately.

        if event_type == "MANUAL_SOS":

            event = emergency_service.trigger_emergency(

                db=db,

                user=current_user,

                notifier=notifier,

                event_type=event_type,

                latitude=None,
                longitude=None,
            )


        # Fall detection uses confirmation flow.

        else:

            event = (
                emergency_service.create_pending_emergency(

                    db=db,

                    user=current_user,

                    event_type=event_type,

                    latitude=None,
                    longitude=None,
                )
            )


        emergency_created = True

        emergency_id = event.id


    return FallDetectionResponse(

        sensor_reading_id=reading.id,

        fall_detected=analysis[
            "fall_detected"
        ],

        emergency_detected=analysis[
            "emergency_detected"
        ],

        event_type=analysis[
            "event_type"
        ],

        confidence=analysis[
            "confidence"
        ],

        acceleration_magnitude=analysis[
            "acceleration_magnitude"
        ],

        gyro_magnitude=analysis[
            "gyro_magnitude"
        ],

        severity=analysis[
            "severity"
        ],

        reason=analysis[
            "reason"
        ],

        emergency_created=emergency_created,

        emergency_id=emergency_id,
    )


# ============================================================
# MANUAL ESCALATION
# ============================================================

@router.post(
    "/{emergency_id}/escalate",
    response_model=EmergencyEventResponse,
)
def escalate_emergency(

    emergency_id: int,

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

    event = emergency_service.escalate_emergency(

        db=db,

        user=current_user,

        notifier=notifier,

        emergency_id=emergency_id,
    )


    if not event:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency not found",
        )


    return event