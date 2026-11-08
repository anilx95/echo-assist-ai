import shutil
import tempfile

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from app.services.detection_deduplication_service import (
    detection_deduplication_service,
)
from app.services.frame_pipeline_service import (
    frame_pipeline_service,
)

from app.services.realtime_pipeline_service import (
    realtime_pipeline_service,
)

from sqlalchemy.orm import Session


from app.database import get_db

from app.models.device import Device
from app.models.detection_event import DetectionEvent
from app.models.risk_event import RiskEvent
from app.models.sensor_reading import SensorReading
from app.models.user import User


from app.schemas.ai import (
    DetectRequest,
    DetectResponse,
    RiskRequest,
    RiskResponse,
    SceneDescriptionRequest,
    SceneDescriptionResponse,
)


from app.services.ai_service import (
    AIService,
    get_ai_service,
)

from app.services.auth_service import (
    get_current_user,
)

from app.services.object_detection_service import (
    object_detection_service,
)

from app.services.depth_estimation_service import (
    depth_estimation_service,
)

from app.services.decision_engine_service import (
    decision_engine_service,
)

from app.services.risk_prediction_service import (
    risk_prediction_service,
)

from app.services.sensor_fusion_service import (
    sensor_fusion_service,
)

from app.services.segmentation_service import (
    segmentation_service,
)

from app.services.path_decision_service import (
    path_decision_service,
)

from app.services.object_distance_fusion_service import (
    object_distance_fusion_service,
)

from app.services.temporal_tracking_service import (
    temporal_tracking_service,
)

from app.services.class_stabilization_service import (
    class_stabilization_service,
)

from app.services.motion_risk_service import (
    motion_risk_service,
)

from app.services.global_scene_decision_service import (
    global_scene_decision_service,
)


router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


# ============================================================
# BASIC OBJECT DETECTION
# ============================================================

@router.post(
    "/detect",
    response_model=DetectResponse,
)
def detect(
    payload: DetectRequest,

    ai_service: AIService = Depends(
        get_ai_service
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    detections = (
        ai_service.detect_objects()
    )

    return DetectResponse(
        detections=detections,
        mock_mode=ai_service.mock_mode,
    )


# ============================================================
# RULE-BASED RISK ENDPOINT
# ============================================================

@router.post(
    "/risk",
    response_model=RiskResponse,
)
def predict_risk(
    payload: RiskRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    distance = (
        payload.fused_distance_m
    )

    obj = (
        payload.object_name.lower()
    )


    if (
        obj == "stairs"
        and distance < 3
    ):

        risk_level = "DANGER"


    elif (
        payload.is_approaching
        and obj
        in {
            "car",
            "bus",
            "truck",
            "motorcycle",
            "bicycle",
        }
    ):

        risk_level = "DANGER"


    elif distance < 1.0:

        risk_level = "DANGER"


    elif distance < 2.0:

        risk_level = "WARNING"


    elif distance <= 4.0:

        if obj in {
            "person",
            "car",
            "pole",
            "stairs",
        }:

            risk_level = "WARNING"

        else:

            risk_level = "SAFE"


    else:

        risk_level = "SAFE"


    if risk_level == "DANGER":

        message = (
            f"{payload.object_name.capitalize()} "
            "ahead. Move away."
        )

        priority = 3

        vibration = "danger"


    elif risk_level == "WARNING":

        message = (
            f"{payload.object_name.capitalize()} "
            f"nearby, {distance:.1f} meters."
        )

        priority = 2

        vibration = "warning"


    else:

        message = ""

        priority = 0

        vibration = "none"


    event = RiskEvent(

        user_id=current_user.id,

        object_name=(
            payload.object_name
        ),

        fused_distance_m=distance,

        direction=(
            payload.direction
        ),

        risk_level=risk_level,

        message=message,
    )


    db.add(event)

    db.commit()


    return RiskResponse(

        object_name=(
            payload.object_name
        ),

        fused_distance_m=distance,

        direction=(
            payload.direction
        ),

        risk_level=risk_level,

        message=message,

        priority=priority,

        vibration_pattern=(
            vibration
        ),
    )


@router.get("/risk/history")
def risk_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the signed-in user's real recorded risk evaluations."""
    bounded_limit = max(1, min(limit, 100))
    records = (
        db.query(RiskEvent)
        .filter(RiskEvent.user_id == current_user.id)
        .order_by(RiskEvent.created_at.desc())
        .limit(bounded_limit)
        .all()
    )
    return [
        {
            "id": item.id,
            "object_name": item.object_name,
            "fused_distance_m": item.fused_distance_m,
            "direction": item.direction,
            "risk_level": item.risk_level,
            "message": item.message,
            "created_at": item.created_at,
        }
        for item in records
    ]


# ============================================================
# SCENE DESCRIPTION
# ============================================================

@router.post(
    "/scene-description",
    response_model=SceneDescriptionResponse,
)
def scene_description(
    payload: SceneDescriptionRequest,

    ai_service: AIService = Depends(
        get_ai_service
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return SceneDescriptionResponse(

        description=(
            ai_service.describe_scene()
        ),

        mock_mode=(
            ai_service.mock_mode
        ),
    )


# ============================================================
# RISK MODEL TEST
# ============================================================

@router.get(
    "/risk/test"
)
def test_risk_prediction(

    object_type: str = "car",

    distance_cm: float = 80,

    speed: float = 2.0,

    direction: str = "center",

    surface_risk: int = 1,

    lighting_risk: int = 1,
):

    return (
        risk_prediction_service
        .predict(

            object_type=object_type,

            distance_cm=distance_cm,

            speed=speed,

            direction=direction,

            surface_risk=surface_risk,

            lighting_risk=lighting_risk,
        )
    )


# ============================================================
# DECISION ENGINE TEST
# ============================================================

@router.get(
    "/decision/test"
)
def test_decision_engine(

    object_type: str = "car",

    distance_cm: float = 80,

    speed: float = 2.0,

    direction: str = "center",

    surface_risk: int = 1,

    lighting_risk: int = 1,
):

    risk_result = (
        risk_prediction_service
        .predict(

            object_type=object_type,

            distance_cm=distance_cm,

            speed=speed,

            direction=direction,

            surface_risk=surface_risk,

            lighting_risk=lighting_risk,
        )
    )


    decision = (
        decision_engine_service
        .decide(

            object_type=object_type,

            distance_cm=distance_cm,

            direction=direction,

            risk_level=(
                risk_result[
                    "risk_level"
                ]
            ),

            confidence=(
                risk_result[
                    "confidence"
                ]
            ),
        )
    )


    return {

        "risk_prediction": (
            risk_result
        ),

        "decision": (
            decision
        ),
    }


# ============================================================
# COMPLETE IMAGE AI PIPELINE
# ============================================================

@router.post(
    "/pipeline/image"
)
async def run_image_pipeline(

    image: UploadFile = File(...),

    speed: float = 0.0,

    surface_risk: int = 1,

    lighting_risk: int = 1,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):


    # ========================================================
    # VALIDATE IMAGE
    # ========================================================

    if not image.filename:

        raise HTTPException(

            status_code=400,

            detail=(
                "Image file is required."
            ),
        )


    suffix = (
        Path(image.filename).suffix
        or ".jpg"
    )


    # ========================================================
    # CREATE TEMPORARY IMAGE FILE
    # ========================================================

    with tempfile.NamedTemporaryFile(

        delete=False,

        suffix=suffix,

    ) as temp_file:

        shutil.copyfileobj(

            image.file,

            temp_file,
        )

        temp_path = (
            temp_file.name
        )


    try:

        # ==================================================
        # STEP 1: YOLO11 OBJECT DETECTION
        # ==================================================

        raw_detections = (
            object_detection_service
            .detect_image(
                temp_path
            )
        )


        # ==================================================
        # STEP 1.1: DETECTION DEDUPLICATION
        # ==================================================

        detections = (
            detection_deduplication_service
            .deduplicate(
                detections=raw_detections,
            )
        )


        if not detections:

            return {

                "pipeline_status": (
                    "NO_OBJECTS_DETECTED"
                ),

                "models_used": [
                    "YOLO11 Nano",
                ],

                "raw_objects_detected": len(
                    raw_detections
                ),

                "objects_detected": 0,

                "duplicates_removed": len(
                    raw_detections
                ),

                "scene_decision": {

                    "action": "CONTINUE",

                    "voice_message": (
                        "No immediate obstacle "
                        "detected."
                    ),

                    "vibration": "NONE",

                    "priority": 4,
                },

                "primary_warning": None,

                "all_results": [],
            }


        # ==================================================
        # STEP 2: MIDAS DEPTH ESTIMATION
        # ==================================================

        depth_map = (
            depth_estimation_service
            .generate_depth_map(
                temp_path
            )
        )


        # ==================================================
        # STEP 3: FAST-SCNN SEGMENTATION
        # ==================================================

        segmentation_result = (
            segmentation_service
            .segment_image(
                temp_path
            )
        )

        walkability = (
            segmentation_result[
                "walkability"
            ]
        )


        # ==================================================
        # STEP 4: GET LATEST SENSOR READING
        # ==================================================

        sensor_reading = (

            db.query(
                SensorReading
            )

            .join(
                Device,
                SensorReading.device_id
                == Device.id,
            )

            .filter(
                Device.user_id
                == current_user.id
            )

            .order_by(
                SensorReading.id.desc()
            )

            .first()
        )


        if sensor_reading is None:

            raise HTTPException(

                status_code=404,

                detail=(
                    "No sensor reading found "
                    "for this user."
                ),
            )


        # ==================================================
        # TOF + ULTRASONIC SENSOR FUSION
        # ==================================================

        fusion = (
            sensor_fusion_service
            .fuse_distance(
                tof_mm=(
                    sensor_reading.tof_mm
                ),
                ultrasonic_cm=(
                    sensor_reading.ultrasonic_cm
                ),
            )
        )


        fused_distance = (
            fusion[
                "distance_cm"
            ]
        )


        if fused_distance is None:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Unable to calculate "
                    "fused distance."
                ),
            )


        # ==================================================
        # STEP 5: COLLECT MIDAS DEPTH FOR EVERY OBJECT
        # ==================================================

        depth_objects = []


        for detection in detections:

            relative_depth = (
                depth_estimation_service
                .get_object_depth(

                    depth_map=depth_map,

                    bounding_box=(
                        detection[
                            "bounding_box"
                        ]
                    ),
                )
            )


            depth_objects.append({

                "detection": (
                    detection
                ),

                "object_type": (
                    detection[
                        "object_type"
                    ]
                ),

                "direction": (
                    detection[
                        "direction"
                    ]
                ),

                "relative_depth": (
                    relative_depth
                ),
            })


        # ==================================================
        # STEP 6: PER-OBJECT DISTANCE FUSION
        # ==================================================

        distance_objects = (
            object_distance_fusion_service
            .estimate_distances(

                objects=(
                    depth_objects
                ),

                physical_distance_cm=(
                    fused_distance
                ),
            )
        )


        # ==================================================
        # STEP 7: INITIAL RISK FOR EVERY OBJECT
        # ==================================================

        pipeline_results = []


        for item in distance_objects:

            detection = (
                item[
                    "detection"
                ]
            )


            object_distance = (
                item.get(
                    "estimated_distance_cm"
                )
            )


            if object_distance is None:

                object_distance = (
                    fused_distance
                )


            # ----------------------------------------------
            # RANDOM FOREST INITIAL RISK
            # ----------------------------------------------

            risk = (
                risk_prediction_service
                .predict(

                    object_type=(
                        detection[
                            "object_type"
                        ]
                    ),

                    distance_cm=(
                        object_distance
                    ),

                    speed=speed,

                    direction=(
                        detection[
                            "direction"
                        ]
                    ),

                    surface_risk=(
                        surface_risk
                    ),

                    lighting_risk=(
                        lighting_risk
                    ),
                )
            )


            pipeline_results.append({

                "detection": (
                    detection
                ),


                "depth_estimation": {

                    "model": (
                        "MiDaS_small"
                    ),

                    "relative_depth": (
                        item.get(
                            "relative_depth"
                        )
                    ),

                    "depth_rank": (
                        item.get(
                            "depth_rank"
                        )
                    ),

                    "note": (
                        "MiDaS provides relative "
                        "inverse depth."
                    ),
                },


                "distance_estimation": {

                    "estimated_distance_cm": (
                        object_distance
                    ),

                    "distance_source": (
                        item.get(
                            "distance_source"
                        )
                    ),

                    "distance_confidence": (
                        item.get(
                            "distance_confidence"
                        )
                    ),

                    "physical_sensor_anchor_cm": (
                        fused_distance
                    ),
                },


                "risk_prediction": (
                    risk
                ),
            })


        # ==================================================
        # STEP 8: TEMPORAL OBJECT TRACKING
        # ==================================================

        pipeline_results = (
            temporal_tracking_service
            .process_frame(

                objects=(
                    pipeline_results
                )
            )
        )


        # ==================================================
        # STEP 9: MOTION RISK + FINAL OBJECT DECISION
        # ==================================================

        final_pipeline_results = []


        for item in pipeline_results:

            detection = (
                item[
                    "detection"
                ]
            )


            object_distance = (

                item[
                    "distance_estimation"
                ][
                    "estimated_distance_cm"
                ]
            )


            tracking = (
                item[
                    "tracking"
                ]
            )


            initial_risk = (
                item[
                    "risk_prediction"
                ]
            )


            # ----------------------------------------------
            # MOTION-AWARE RISK ESCALATION
            # ----------------------------------------------

            motion_adjusted_risk = (
                motion_risk_service
                .evaluate(

                    risk_result=(
                        initial_risk
                    ),

                    tracking_result=(
                        tracking
                    ),
                )
            )


            # ----------------------------------------------
            # RULE-BASED DECISION
            # ----------------------------------------------

            decision = (
                decision_engine_service
                .decide(

                    object_type=(
                        detection[
                            "object_type"
                        ]
                    ),

                    distance_cm=(
                        object_distance
                    ),

                    direction=(
                        detection[
                            "direction"
                        ]
                    ),

                    risk_level=(
                        motion_adjusted_risk[
                            "risk_level"
                        ]
                    ),

                    confidence=(
                        motion_adjusted_risk[
                            "confidence"
                        ]
                    ),
                )
            )


            # ----------------------------------------------
            # PATH-AWARE DECISION
            # ----------------------------------------------

            final_decision = (
                path_decision_service
                .refine_decision(

                    decision=(
                        decision
                    ),

                    walkability=(
                        walkability
                    ),
                )
            )


            final_pipeline_results.append({

                **item,

                "risk_prediction": (
                    motion_adjusted_risk
                ),

                "decision": (
                    final_decision
                ),
            })


        pipeline_results = (
            final_pipeline_results
        )


        # ==================================================
        # STEP 10: SORT BY FINAL PRIORITY
        # ==================================================

        pipeline_results.sort(

            key=lambda item:
            item[
                "decision"
            ][
                "priority"
            ]
        )


        # ==================================================
        # STEP 11: GLOBAL SCENE SAFETY DECISION
        # ==================================================

        scene_decision = (
            global_scene_decision_service
            .decide(

                pipeline_results=(
                    pipeline_results
                ),

                walkability=(
                    walkability
                ),

                sensor_fusion=(
                    fusion
                ),
            )
        )


        # ==================================================
        # STEP 12: FINAL RESPONSE
        # ==================================================

        return {

            "pipeline_status": (
                "SUCCESS"
            ),


            "models_used": [

                "YOLO11 Nano",

                "MiDaS Small",

                "Fast-SCNN",

                "ToF-Ultrasonic Sensor Fusion",

                "Per-Object Distance Fusion",

                "Random Forest",

                "Temporal Object Tracking",

                "Motion-Aware Risk Escalation",

                "Rule-Based Decision Engine",

                "Path-Aware Decision Layer",

                "Global Scene Safety Decision Engine",
            ],


            "sensor_reading_id": (
                sensor_reading.id
            ),


            "sensor_fusion": (
                fusion
            ),


            "walkable_path_analysis": {

                "model": (
                    "Fast-SCNN"
                ),

                **walkability,
            },


            "raw_objects_detected": len(
                raw_detections
            ),


            "objects_detected": len(
                detections
            ),


            "duplicates_removed": (
                len(raw_detections)
                - len(detections)
            ),


            "scene_decision": (
                scene_decision
            ),


            "primary_warning": (

                pipeline_results[0]

                if pipeline_results

                else None
            ),


            "all_results": (
                pipeline_results
            ),
        }


    finally:

        Path(
            temp_path
        ).unlink(
            missing_ok=True
        )


# ============================================================
# REAL-TIME FRAME PIPELINE
# ============================================================

@router.post("/pipeline/realtime-frame")
async def process_realtime_frame(
    file: UploadFile = File(...),
    speed: float = 0.0,
    surface_risk: int = 0,
    lighting_risk: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Image file is required.")

    if not realtime_pipeline_service.should_process_frame(
        user_id=current_user.id,
        minimum_interval_seconds=0.3
    ):
        return {
            "pipeline_status": "FRAME_SKIPPED",
            "reason": "Frame arrived before minimum processing interval.",
            "latest_result": realtime_pipeline_service.get_latest_result(current_user.id),
        }

    frame_info = realtime_pipeline_service.start_frame(current_user.id)
    suffix = Path(file.filename).suffix or ".jpg"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        result = frame_pipeline_service.process_frame(
            image_path=temp_path,
            db=db,
            user_id=current_user.id,
            speed=speed,
            surface_risk=surface_risk,
            lighting_risk=lighting_risk,
        )

        result["realtime"] = {
            "frame_number": frame_info["frame_number"],
            "timestamp": frame_info["timestamp"],
        }

        realtime_pipeline_service.store_result(current_user.id, result)
        return result

    finally:
        Path(temp_path).unlink(missing_ok=True)


@router.get("/history")
def detection_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 100))
    records = db.query(DetectionEvent).filter(DetectionEvent.user_id == current_user.id).order_by(
        DetectionEvent.created_at.desc()
    ).limit(limit).all()
    return [{
        "id": item.id, "class_name": item.class_name, "confidence": item.confidence,
        "position": item.position, "created_at": item.created_at,
    } for item in records]


@router.get("/pipeline/realtime/latest")
def get_latest_realtime_result(
    current_user: User = Depends(get_current_user),
):
    result = realtime_pipeline_service.get_latest_result(current_user.id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No real-time frame has been processed yet.",
        )

    return result


@router.get("/pipeline/realtime/history")
def get_realtime_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 30))
    return {
        "frames": realtime_pipeline_service.get_history(current_user.id, limit=limit)
    }


@router.post("/pipeline/realtime/reset")
def reset_realtime_session(
    current_user: User = Depends(get_current_user),
):
    realtime_pipeline_service.reset(current_user.id)
    temporal_tracking_service.reset()
    class_stabilization_service.reset()

    return {
        "status": "SUCCESS",
        "message": (
            "Real-time pipeline, temporal tracking, "
            "and class stabilization state reset."
        ),
    }
