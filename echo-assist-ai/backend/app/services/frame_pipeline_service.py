from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.navigation_command_service import (
    navigation_command_service,
)

from app.models.device import Device
from app.models.detection_event import DetectionEvent
from app.models.sensor_reading import SensorReading
from app.services.class_stabilization_service import (
    class_stabilization_service,
)
from app.services.scene_command_stabilization_service import (
    scene_command_stabilization_service,
)

from app.services.object_detection_service import (
    object_detection_service,
)
from app.services.detection_deduplication_service import (
    detection_deduplication_service,
)
from app.services.depth_estimation_service import (
    depth_estimation_service,
)
from app.services.segmentation_service import (
    segmentation_service,
)
from app.services.sensor_fusion_service import (
    sensor_fusion_service,
)
from app.services.object_distance_fusion_service import (
    object_distance_fusion_service,
)
from app.services.risk_prediction_service import (
    risk_prediction_service,
)
from app.services.temporal_tracking_service import (
    temporal_tracking_service,
)
from app.services.motion_risk_service import (
    motion_risk_service,
)
from app.services.decision_engine_service import (
    decision_engine_service,
)
from app.services.path_decision_service import (
    path_decision_service,
)
from app.services.global_scene_decision_service import (
    global_scene_decision_service,
)
from app.services.cane_output_service import (
    cane_output_service,
)


class FramePipelineService:

    def __init__(self):
        self.ready = True


    def process_frame(
        self,
        image_path: str,
        db: Session,
        user_id: int,
        speed: float = 0.0,
        surface_risk: int = 0,
        lighting_risk: int = 0,
    ) -> dict:

        # ==================================================
        # STEP 1: YOLO11 OBJECT DETECTION
        # ==================================================

        raw_detections = (
            object_detection_service
            .detect_image(
                image_path
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

        # Persist the raw vision observations with no claim that the distance
        # is camera-measured. Risk/distance provenance is added downstream.
        for detection in detections:
            box = detection.get("bounding_box", {})
            db.add(DetectionEvent(
                user_id=user_id,
                class_name=detection.get("object_type", "unknown"),
                confidence=float(detection.get("confidence", 0.0)),
                position=detection.get("direction", "center"),
                bbox_x1=box.get("x1"), bbox_y1=box.get("y1"),
                bbox_x2=box.get("x2"), bbox_y2=box.get("y2"),
            ))
        if detections:
            db.commit()


        # ==================================================
        # NO OBJECT RESPONSE
        # ==================================================

        if not detections:

            scene_decision = {
                "action": "CONTINUE",
                "voice_message": (
                    "No immediate obstacle detected."
                ),
                "vibration": "NONE",
                "priority": 4,
                "reason": (
                    "No obstacle detected in the current frame."
                ),
            }

            # ==================================================
            # SCENE COMMAND STABILIZATION
            # ==================================================

            stabilized_scene_decision = (
                scene_command_stabilization_service
                .stabilize(
                    scene_decision=scene_decision
                )
            )

            # ==================================================
            # SMART CANE OUTPUT GENERATION
            # ==================================================

            cane_output = (
                cane_output_service
                .generate_output(
                    scene_decision=(
                        stabilized_scene_decision
                    )
                )
            )


                        # ==================================================
            # STEP XX: BUILD UNIVERSAL NAVIGATION COMMAND
            # ==================================================

            navigation_command = (
                navigation_command_service.build_command(
                    scene_decision=scene_decision,
                    stabilized_scene_decision=stabilized_scene_decision,
                    cane_output=cane_output,
                    primary_warning=None,
                )
            )


            return {
                "pipeline_status": (
                    "NO_OBJECTS_DETECTED"
                ),

                "models_used": [
                    "YOLO11 Nano",
                    "Detection Deduplication",
                    "Scene Command Stabilization",
                    "Smart Cane Output Controller",
                ],

                "raw_objects_detected": len(
                    raw_detections
                ),

                "objects_detected": 0,

                "duplicates_removed": len(
                    raw_detections
                ),

                "scene_decision": (
                    scene_decision
                ),

                "stabilized_scene_decision": (
                    stabilized_scene_decision
                ),

                "cane_output": (
                    cane_output
                ),

                "navigation_command": (
                    navigation_command
                ),

                "primary_warning": None,

                "all_results": [],
            }


        # ==================================================
        # STEP 2: MIDAS DEPTH ESTIMATION
        # ==================================================

        depth_map = (
            depth_estimation_service
            .generate_depth_map(
                image_path
            )
        )


        # ==================================================
        # STEP 3: FAST-SCNN SEGMENTATION
        # ==================================================

        segmentation_result = (
            segmentation_service
            .segment_image(
                image_path
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
                == user_id
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
        # STEP 4.1: TOF + ULTRASONIC SENSOR FUSION
        # ==================================================

        fusion = (
            sensor_fusion_service
            .fuse_distance(

                tof_mm=(
                    sensor_reading.tof_mm
                ),

                ultrasonic_cm=(
                    sensor_reading
                    .ultrasonic_cm
                ),
            )
        )


        fused_distance = fusion[
            "distance_cm"
        ]


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

                "detection": detection,

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

                objects=depth_objects,

                physical_distance_cm=(
                    fused_distance
                ),
            )
        )


        # ==================================================
        # STEP 7: BUILD PRE-RISK OBJECT RESULTS
        # ==================================================

        pipeline_results = []

        for item in distance_objects:
            detection = item["detection"]
            object_distance = item.get("estimated_distance_cm")

            if object_distance is None:
                object_distance = fused_distance

            pipeline_results.append({
                "detection": detection,
                "depth_estimation": {
                    "model": "MiDaS_small",
                    "relative_depth": item.get("relative_depth"),
                    "depth_rank": item.get("depth_rank"),
                    "note": "MiDaS provides relative inverse depth.",
                },
                "distance_estimation": {
                    "estimated_distance_cm": object_distance,
                    "distance_source": item.get("distance_source"),
                    "distance_confidence": item.get("distance_confidence"),
                    "physical_sensor_anchor_cm": fused_distance,
                },
            })


        # ==================================================
        # STEP 8: TEMPORAL OBJECT TRACKING
        # ==================================================

        pipeline_results = (
            temporal_tracking_service.process_frame(
                objects=pipeline_results
            )
        )


        # ==================================================
        # STEP 9: USE TEMPORALLY STABILIZED DISTANCE
        # ==================================================

        for item in pipeline_results:
            tracking = item.get("tracking", {})
            raw_distance = item["distance_estimation"].get(
                "estimated_distance_cm"
            )
            smoothed_distance = tracking.get(
                "smoothed_distance_cm"
            )

            if smoothed_distance is not None:
                risk_distance = smoothed_distance
                distance_mode = "temporal_smoothed_distance"
            else:
                risk_distance = raw_distance
                distance_mode = "raw_fused_distance"

            item["distance_estimation"][
                "raw_estimated_distance_cm"
            ] = raw_distance

            item["distance_estimation"][
                "risk_distance_cm"
            ] = risk_distance

            item["distance_estimation"][
                "risk_distance_source"
            ] = distance_mode


        # ==================================================
        # STEP 10: TEMPORAL CLASS STABILIZATION
        # ==================================================

        pipeline_results = (
            class_stabilization_service.stabilize(
                objects=pipeline_results
            )
        )


        # ==================================================
        # STEP 11: RANDOM FOREST RISK + MOTION RISK
        #          + FINAL OBJECT DECISION
        # ==================================================

        final_pipeline_results = []


        for item in pipeline_results:

            detection = item[
                "detection"
            ]


            object_distance = (

                item[
                    "distance_estimation"
                ][
                    "estimated_distance_cm"
                ]
            )


            tracking = item[
                "tracking"
            ]


            risk_distance = (
                item["distance_estimation"].get(
                    "risk_distance_cm",
                    object_distance,
                )
            )


            # ----------------------------------------------
            # RANDOM FOREST RISK PREDICTION
            # ----------------------------------------------

            initial_risk = (
                risk_prediction_service.predict(
                    object_type=detection["object_type"],
                    distance_cm=risk_distance,
                    speed=speed,
                    direction=detection["direction"],
                    surface_risk=surface_risk,
                    lighting_risk=lighting_risk,
                )
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
            # RULE-BASED DECISION ENGINE
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
                        risk_distance
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
            # PATH-AWARE DECISION REFINEMENT
            # ----------------------------------------------

            final_decision = (

                path_decision_service
                .refine_decision(

                    decision=decision,

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
        # STEP 12: SORT BY FINAL PRIORITY
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
        # STEP 13: GLOBAL SCENE SAFETY DECISION
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
        # STEP 14: SCENE COMMAND STABILIZATION
        # ==================================================

        stabilized_scene_decision = (
            scene_command_stabilization_service
            .stabilize(
                scene_decision=scene_decision
            )
        )

        # ==================================================
        # STEP 15: SMART CANE OUTPUT GENERATION
        # ==================================================

        cane_output = (
            cane_output_service
            .generate_output(
                scene_decision=(
                    stabilized_scene_decision
                )
            )
        )

                # ==================================================
        # STEP 16: BUILD UNIVERSAL NAVIGATION COMMAND
        # ==================================================

        navigation_command = (
            navigation_command_service.build_command(
                scene_decision=scene_decision,
                stabilized_scene_decision=stabilized_scene_decision,
                cane_output=cane_output,
                primary_warning=(
                    pipeline_results[0]
                    if pipeline_results
                    else None
                ),
            )
        )

        # ==================================================
        # STEP 17: FINAL RESPONSE
        # ==================================================

        return {

            "pipeline_status": (
                "SUCCESS"
            ),


            "models_used": [

                "YOLO11 Nano",

                "Detection Deduplication",

                "MiDaS Small",

                "Fast-SCNN",

                "ToF-Ultrasonic Sensor Fusion",

                "Per-Object Distance Fusion",

                "Random Forest",

                "Temporal Object Tracking",

                "Temporal Distance Stabilization",

                "Temporal Class Stabilization",

                "Motion-Aware Risk Escalation",

                "Rule-Based Decision Engine",

                "Path-Aware Decision Layer",

                "Global Scene Safety Decision Engine",

                "Scene Command Stabilization",

                "Smart Cane Output Controller",
            ],


            "sensor_reading_id": (
                sensor_reading.id
            ),


            "sensor_fusion": (
                fusion
            ),


            "walkable_path_analysis": {

                "model": "Fast-SCNN",

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

            "stabilized_scene_decision": (
                stabilized_scene_decision
            ),

            "cane_output": (
                cane_output
            ),

            "navigation_command": (
                navigation_command
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


frame_pipeline_service = (
    FramePipelineService()
)
