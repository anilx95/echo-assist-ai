from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.models.user import User

from app.schemas.sensor import (
    SensorPacket,
    SensorReadingResponse,
)

from app.services.auth_service import get_current_user
from app.services.sensor_fusion_service import sensor_fusion_service
from app.services.fall_detection_service import fall_detection_service
from app.services.emergency_service import emergency_service
from app.services.notification_service import (
    NotificationService,
    get_notification_service,
)

from app.services.emergency_countdown_service import (
    emergency_countdown_task,
)


router = APIRouter(
    prefix="/sensors",
    tags=["sensors"],
)


# ============================================================
# RECEIVE SENSOR DATA
# ============================================================

@router.post(
    "/data",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_sensor_data(
    packet: SensorPacket,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    notifier: NotificationService = Depends(get_notification_service),
):

    # --------------------------------------------------------
    # FIND DEVICE
    # --------------------------------------------------------

    device = (
        db.query(Device)
        .filter(Device.device_id == packet.device_id)
        .first()
    )


    # --------------------------------------------------------
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device is not registered. Register it before sending sensor data.",
        )


    # --------------------------------------------------------
    # SECURITY CHECK
    # --------------------------------------------------------

    if device.user_id != current_user.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device belongs to another user",
        )


    # --------------------------------------------------------
    # UPDATE DEVICE CONNECTION STATUS
    # --------------------------------------------------------

    device.connection_status = "connected"
    device.last_connected_at = datetime.now(timezone.utc)
    device.battery_percent = packet.battery_percent
    device.sensor_health = "healthy"


    # --------------------------------------------------------
    # CREATE SENSOR READING
    # --------------------------------------------------------

    reading = SensorReading(

        device_id=device.id,

        ultrasonic_cm=packet.ultrasonic_cm,
        tof_mm=packet.tof_mm,

        accel_x=packet.accel_x,
        accel_y=packet.accel_y,
        accel_z=packet.accel_z,

        gyro_x=packet.gyro_x,
        gyro_y=packet.gyro_y,
        gyro_z=packet.gyro_z,

        sos_pressed=packet.sos_pressed,

        battery_percent=packet.battery_percent,

        device_timestamp=packet.timestamp,
    )


    db.add(reading)

    # Save sensor reading and device status.

    db.commit()
    db.refresh(reading)


    # ========================================================
    # AUTOMATIC FALL DETECTION
    # ========================================================

    fall_analysis = fall_detection_service.analyze(

        accel_x=reading.accel_x,
        accel_y=reading.accel_y,
        accel_z=reading.accel_z,

        gyro_x=reading.gyro_x,
        gyro_y=reading.gyro_y,
        gyro_z=reading.gyro_z,

        sos_pressed=reading.sos_pressed,
    )


    # ========================================================
    # CREATE PENDING EMERGENCY
    # ========================================================

    if fall_analysis["emergency_detected"]:

        event_type = fall_analysis["event_type"]
        if event_type == "MANUAL_SOS":
            emergency_event = emergency_service.trigger_emergency(
                db=db,
                user=current_user,
                notifier=notifier,
                event_type=event_type,
                # The ESP32 protocol currently does not carry GPS coordinates.
                latitude=None,
                longitude=None,
            )
        else:
            emergency_event = emergency_service.create_pending_emergency(
                db=db,
                user=current_user,
                event_type=event_type,
                # The ESP32 protocol currently does not carry GPS coordinates.
                latitude=None,
                longitude=None,
            )


        # ----------------------------------------------------
        # START AUTOMATIC ESCALATION COUNTDOWN
        # ----------------------------------------------------

        if (
            emergency_event.status
            == "PENDING_CONFIRMATION"
        ):

            background_tasks.add_task(

                emergency_countdown_task,

                emergency_id=emergency_event.id,

                user_id=current_user.id,

                countdown_seconds=30,
            )


    return reading


# ============================================================
# GET LATEST SENSOR READING
# ============================================================

@router.get(
    "/latest",
    response_model=SensorReadingResponse,
)
def get_latest_reading(

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

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

            detail="No sensor data yet",
        )


    return reading


@router.get(
    "/history",
    response_model=list[SensorReadingResponse],
)
def get_sensor_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return only the signed-in user's recent sensor readings."""
    bounded_limit = max(1, min(limit, 200))
    return (
        db.query(SensorReading)
        .join(Device, Device.id == SensorReading.device_id)
        .filter(Device.user_id == current_user.id)
        .order_by(SensorReading.received_at.desc())
        .limit(bounded_limit)
        .all()
    )


# ============================================================
# SENSOR FUSION
# ============================================================

@router.get("/fusion/latest")
def get_latest_fusion(

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

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

            detail=(
                "No sensor data available for fusion"
            ),
        )


    fusion_result = (
        sensor_fusion_service.fuse_distance(

            tof_mm=reading.tof_mm,

            ultrasonic_cm=reading.ultrasonic_cm,
        )
    )


    return {

        "reading_id": reading.id,

        "device_id": reading.device_id,

        "fusion": fusion_result,
    }
