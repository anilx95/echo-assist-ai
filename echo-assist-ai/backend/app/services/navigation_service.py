import math
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.navigation_route import NavigationRoute
from app.schemas.navigation import RouteStep
from app.services.routing_service import routing_service


class NavigationService:

    def __init__(self):
        self.active_routes = {}


    # ========================================================
    # DISTANCE CALCULATION
    # ========================================================

    def calculate_distance(
        self,
        lat1,
        lng1,
        lat2,
        lng2,
    ):

        radius = 6371000

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        delta_phi = math.radians(
            lat2 - lat1
        )

        delta_lambda = math.radians(
            lng2 - lng1
        )

        a = (
            math.sin(delta_phi / 2) ** 2
            +
            math.cos(phi1)
            * math.cos(phi2)
            * math.sin(delta_lambda / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )

        return round(
            radius * c,
            2,
        )


    # ========================================================
    # DIRECTION CONVERSION
    # ========================================================

    def get_direction(
        self,
        instruction: str,
        step_type=None,
    ):

        text = instruction.lower()

        if "sharp left" in text:
            return "SHARP_LEFT"

        if "sharp right" in text:
            return "SHARP_RIGHT"

        if "slight left" in text:
            return "SLIGHT_LEFT"

        if "slight right" in text:
            return "SLIGHT_RIGHT"

        if (
            "turn left" in text
            or "keep left" in text
        ):
            return "LEFT"

        if (
            "turn right" in text
            or "keep right" in text
        ):
            return "RIGHT"

        if (
            "arrive" in text
            or "destination" in text
        ):
            return "ARRIVE"

        if (
            "head" in text
            or "continue" in text
            or "straight" in text
        ):
            return "STRAIGHT"

        return "CONTINUE"


    # ========================================================
    # VOICE INSTRUCTION
    # ========================================================

    def create_voice_instruction(
        self,
        instruction: str,
        distance_m: float,
        direction: str,
    ):

        distance = round(distance_m)

        if direction == "LEFT":
            return (
                f"Turn left and continue for "
                f"{distance} meters."
            )

        if direction == "RIGHT":
            return (
                f"Turn right and continue for "
                f"{distance} meters."
            )

        if direction == "SHARP_LEFT":
            return (
                f"Make a sharp left turn, then continue "
                f"for {distance} meters."
            )

        if direction == "SHARP_RIGHT":
            return (
                f"Make a sharp right turn, then continue "
                f"for {distance} meters."
            )

        if direction == "SLIGHT_LEFT":
            return (
                f"Keep slightly left and continue "
                f"for {distance} meters."
            )

        if direction == "SLIGHT_RIGHT":
            return (
                f"Keep slightly right and continue "
                f"for {distance} meters."
            )

        if direction == "ARRIVE":
            return (
                "You are approaching your destination."
            )

        return (
            f"{instruction}. Continue for "
            f"{distance} meters."
        )


    # ========================================================
    # SERIALIZE ROUTE STEPS
    # ========================================================

    def serialize_steps(
        self,
        steps,
    ):

        return [
            {
                "step_number": step.step_number,
                "instruction": step.instruction,
                "distance_m": step.distance_m,
                "direction": step.direction,
                "voice_instruction": step.voice_instruction,
            }
            for step in steps
        ]


    # ========================================================
    # DESERIALIZE DATABASE STEPS
    # ========================================================

    def deserialize_steps(
        self,
        steps_data,
    ):

        return [
            RouteStep(
                step_number=step["step_number"],
                instruction=step["instruction"],
                distance_m=step["distance_m"],
                direction=step["direction"],
                voice_instruction=step[
                    "voice_instruction"
                ],
            )
            for step in (steps_data or [])
        ]


    # ========================================================
    # LOAD ROUTE FROM DATABASE
    # ========================================================

    def load_route_from_database(
        self,
        db: Session,
        user_id: int,
        route_id: str,
    ):

        db_route = (
            db.query(NavigationRoute)
            .filter(
                NavigationRoute.route_id
                == route_id,
                NavigationRoute.user_id
                == user_id,
            )
            .first()
        )

        if not db_route:
            return None

        steps = self.deserialize_steps(
            db_route.steps
        )

        if not steps:
            return None

        route_data = {

            "route_id": db_route.route_id,

            "destination": db_route.destination,

            "total_distance_m": (
                db_route.total_distance_m
            ),

            "estimated_time_minutes": (
                db_route.estimated_time_minutes
            ),

            "steps": steps,

            "current_step": (
                db_route.current_step
            ),

            "current_instruction": (
                db_route.current_instruction
            ),

            "navigation_status": (
                db_route.navigation_status
            ),

            "mock_mode": db_route.mock_mode,

            "origin_lat": db_route.origin_lat,

            "origin_lng": db_route.origin_lng,

            "destination_lat": (
                db_route.destination_lat
            ),

            "destination_lng": (
                db_route.destination_lng
            ),

            "geometry": (
                db_route.geometry or []
            ),

            "provider_steps": (
                db_route.provider_steps or []
            ),

            "provider": db_route.provider,

            "profile": db_route.profile,

            "previous_route_id": (
                db_route.previous_route_id
            ),

            "replaced_by_route_id": (
                db_route.replaced_by_route_id
            ),

            "rerouted": db_route.rerouted,
        }

        self.active_routes[
            route_id
        ] = route_data

        return route_data


    # ========================================================
    # CREATE REAL WALKING ROUTE
    # ========================================================

    def create_real_route(
        self,
        db: Session,
        user_id: int,
        destination,
        origin_lat,
        origin_lng,
        destination_lat,
        destination_lng,
    ):

        if (
            origin_lat is None
            or origin_lng is None
            or destination_lat is None
            or destination_lng is None
        ):

            raise ValueError(
                "Origin and destination coordinates "
                "are required for real navigation."
            )

        real_route = (
            routing_service.get_walking_route(

                origin_lat=origin_lat,

                origin_lng=origin_lng,

                destination_lat=destination_lat,

                destination_lng=destination_lng,
            )
        )

        route_id = str(
            uuid.uuid4()
        )

        steps = []

        for provider_step in real_route["steps"]:

            instruction = provider_step[
                "instruction"
            ]

            distance_m = provider_step[
                "distance_m"
            ]

            direction = self.get_direction(

                instruction=instruction,

                step_type=provider_step.get(
                    "type"
                ),
            )

            voice_instruction = (
                self.create_voice_instruction(

                    instruction=instruction,

                    distance_m=distance_m,

                    direction=direction,
                )
            )

            steps.append(

                RouteStep(

                    step_number=provider_step[
                        "step_number"
                    ],

                    instruction=instruction,

                    distance_m=distance_m,

                    direction=direction,

                    voice_instruction=(
                        voice_instruction
                    ),
                )
            )

        if not steps:

            raise RuntimeError(
                "Routing provider returned "
                "no navigation steps."
            )

        route_data = {

            "route_id": route_id,

            "destination": destination,

            "total_distance_m": real_route[
                "total_distance_m"
            ],

            "estimated_time_minutes": real_route[
                "estimated_time_minutes"
            ],

            "steps": steps,

            "current_step": 0,

            "current_instruction": (
                steps[0].instruction
            ),

            "navigation_status": "ACTIVE",

            "mock_mode": False,

            "origin_lat": origin_lat,

            "origin_lng": origin_lng,

            "destination_lat": (
                destination_lat
            ),

            "destination_lng": (
                destination_lng
            ),

            "geometry": real_route.get(
                "geometry",
                [],
            ),

            "provider_steps": real_route.get(
                "steps",
                [],
            ),

            "provider": real_route.get(
                "provider"
            ),

            "profile": real_route.get(
                "profile"
            ),

            "previous_route_id": None,

            "replaced_by_route_id": None,

            "rerouted": False,
        }

        self.active_routes[
            route_id
        ] = route_data

        db_route = NavigationRoute(

            route_id=route_id,

            user_id=user_id,

            destination=destination,

            origin_lat=origin_lat,

            origin_lng=origin_lng,

            destination_lat=destination_lat,

            destination_lng=destination_lng,

            total_distance_m=route_data[
                "total_distance_m"
            ],

            estimated_time_minutes=route_data[
                "estimated_time_minutes"
            ],

            current_step=0,

            current_instruction=route_data[
                "current_instruction"
            ],

            navigation_status="ACTIVE",

            provider=route_data.get(
                "provider"
            ),

            profile=route_data.get(
                "profile"
            ),

            geometry=route_data.get(
                "geometry",
                [],
            ),

            steps=self.serialize_steps(
                steps
            ),

            provider_steps=route_data.get(
                "provider_steps",
                [],
            ),

            mock_mode=False,

            rerouted=False,
        )

        try:

            db.add(db_route)

            db.commit()

            db.refresh(db_route)

        except Exception:

            db.rollback()

            self.active_routes.pop(
                route_id,
                None,
            )

            raise

        return route_data


    # ========================================================
    # DEVELOPMENT FALLBACK ROUTE
    # ========================================================

    def create_mock_route(
        self,
        destination,
        origin_lat=None,
        origin_lng=None,
        destination_lat=None,
        destination_lng=None,
    ):

        route_id = str(
            uuid.uuid4()
        )

        if (
            origin_lat is not None
            and origin_lng is not None
            and destination_lat is not None
            and destination_lng is not None
        ):

            direct_distance = (
                self.calculate_distance(

                    origin_lat,
                    origin_lng,

                    destination_lat,
                    destination_lng,
                )
            )

            route_distance = max(
                direct_distance * 1.2,
                80,
            )

        else:

            route_distance = 500

        distances = [

            route_distance * 0.20,

            route_distance * 0.15,

            route_distance * 0.45,

            route_distance * 0.20,
        ]

        steps = [

            RouteStep(
                step_number=1,
                instruction=(
                    f"Head straight for "
                    f"{round(distances[0])} meters."
                ),
                distance_m=round(
                    distances[0],
                    2,
                ),
                direction="STRAIGHT",
                voice_instruction=(
                    f"Go straight for "
                    f"{round(distances[0])} meters."
                ),
            ),

            RouteStep(
                step_number=2,
                instruction=(
                    f"Turn left and continue for "
                    f"{round(distances[1])} meters."
                ),
                distance_m=round(
                    distances[1],
                    2,
                ),
                direction="LEFT",
                voice_instruction=(
                    f"Turn left and continue for "
                    f"{round(distances[1])} meters."
                ),
            ),

            RouteStep(
                step_number=3,
                instruction=(
                    f"Continue straight for "
                    f"{round(distances[2])} meters."
                ),
                distance_m=round(
                    distances[2],
                    2,
                ),
                direction="STRAIGHT",
                voice_instruction=(
                    f"Continue straight for "
                    f"{round(distances[2])} meters."
                ),
            ),

            RouteStep(
                step_number=4,
                instruction=(
                    f"{destination} is ahead."
                ),
                distance_m=round(
                    distances[3],
                    2,
                ),
                direction="ARRIVE",
                voice_instruction=(
                    f"You are approaching "
                    f"{destination}."
                ),
            ),
        ]

        total_distance = sum(
            step.distance_m
            for step in steps
        )

        route_data = {

            "route_id": route_id,

            "destination": destination,

            "total_distance_m": round(
                total_distance,
                2,
            ),

            "estimated_time_minutes": round(
                total_distance / 80,
                1,
            ),

            "steps": steps,

            "current_step": 0,

            "current_instruction": (
                steps[0].instruction
            ),

            "navigation_status": "ACTIVE",

            "mock_mode": True,

            "origin_lat": origin_lat,

            "origin_lng": origin_lng,

            "destination_lat": destination_lat,

            "destination_lng": destination_lng,

            "geometry": [],

            "provider_steps": [],

            "provider": "MOCK",

            "profile": "foot-walking",

            "previous_route_id": None,

            "replaced_by_route_id": None,

            "rerouted": False,
        }

        self.active_routes[
            route_id
        ] = route_data

        return route_data


    # ========================================================
    # FIND NEAREST ROUTE GEOMETRY POINT
    # ========================================================

    def find_nearest_geometry_point(
        self,
        geometry,
        current_latitude,
        current_longitude,
    ):

        if not geometry:

            return {
                "index": 0,
                "distance_m": float("inf"),
            }

        nearest_index = 0

        nearest_distance = float(
            "inf"
        )

        for index, point in enumerate(
            geometry
        ):

            point_lng = point[0]

            point_lat = point[1]

            distance = self.calculate_distance(

                current_latitude,
                current_longitude,

                point_lat,
                point_lng,
            )

            if distance < nearest_distance:

                nearest_distance = distance

                nearest_index = index

        return {

            "index": nearest_index,

            "distance_m": round(
                nearest_distance,
                2,
            ),
        }


    # ========================================================
    # CALCULATE REMAINING ROUTE DISTANCE
    # ========================================================

    def calculate_geometry_remaining_distance(
        self,
        geometry,
        start_index,
    ):

        if (
            not geometry
            or start_index >= len(geometry) - 1
        ):

            return 0.0

        remaining_distance = 0.0

        for index in range(
            start_index,
            len(geometry) - 1,
        ):

            current_point = geometry[index]

            next_point = geometry[index + 1]

            remaining_distance += (
                self.calculate_distance(

                    current_point[1],
                    current_point[0],

                    next_point[1],
                    next_point[0],
                )
            )

        return round(
            remaining_distance,
            2,
        )


    # ========================================================
    # DETERMINE CURRENT STEP
    # ========================================================

    def determine_current_step(
        self,
        route,
        geometry_index,
    ):

        provider_steps = route.get(
            "provider_steps",
            [],
        )

        if not provider_steps:

            return route.get(
                "current_step",
                0,
            )

        for index, step in enumerate(
            provider_steps
        ):

            way_points = step.get(
                "way_points",
                [],
            )

            if len(way_points) != 2:
                continue

            start_index = way_points[0]

            end_index = way_points[1]

            if (
                start_index
                <= geometry_index
                <= end_index
            ):

                return index

        return min(
            len(route["steps"]) - 1,
            len(provider_steps) - 1,
        )


    # ========================================================
    # AUTOMATIC REROUTING
    # ========================================================

    def reroute(
        self,
        db: Session,
        user_id: int,
        old_route_id,
        current_latitude,
        current_longitude,
    ):

        old_route = self.active_routes.get(
            old_route_id
        )

        if not old_route:

            old_route = (
                self.load_route_from_database(

                    db=db,

                    user_id=user_id,

                    route_id=old_route_id,
                )
            )

        if not old_route:
            return None

        destination_lat = old_route.get(
            "destination_lat"
        )

        destination_lng = old_route.get(
            "destination_lng"
        )

        destination = old_route.get(
            "destination"
        )

        if (
            destination_lat is None
            or destination_lng is None
        ):

            raise ValueError(
                "Destination coordinates are unavailable "
                "for rerouting."
            )

        new_route = self.create_real_route(

            db=db,

            user_id=user_id,

            destination=destination,

            origin_lat=current_latitude,

            origin_lng=current_longitude,

            destination_lat=destination_lat,

            destination_lng=destination_lng,
        )

        old_route[
            "navigation_status"
        ] = "REROUTED"

        old_route[
            "replaced_by_route_id"
        ] = new_route[
            "route_id"
        ]

        new_route[
            "previous_route_id"
        ] = old_route_id

        new_route[
            "rerouted"
        ] = True

        old_db_route = (
            db.query(NavigationRoute)
            .filter(
                NavigationRoute.route_id
                == old_route_id,

                NavigationRoute.user_id
                == user_id,
            )
            .first()
        )

        if old_db_route:

            old_db_route.navigation_status = (
                "REROUTED"
            )

            old_db_route.replaced_by_route_id = (
                new_route["route_id"]
            )

        new_db_route = (
            db.query(NavigationRoute)
            .filter(
                NavigationRoute.route_id
                == new_route["route_id"],

                NavigationRoute.user_id
                == user_id,
            )
            .first()
        )

        if new_db_route:

            new_db_route.previous_route_id = (
                old_route_id
            )

            new_db_route.rerouted = True

        try:

            db.commit()

        except Exception:

            db.rollback()

            raise

        return new_route


    # ========================================================
    # GPS-BASED NAVIGATION PROGRESS
    # ========================================================

    def update_progress(
        self,
        route_id,
        current_latitude,
        current_longitude,
        db: Session,
        user_id: int,
        current_step=None,
    ):

        route = self.active_routes.get(
            route_id
        )

        # ----------------------------------------------------
        # RECOVER ROUTE FROM DATABASE AFTER RESTART
        # ----------------------------------------------------

        if not route:

            route = (
                self.load_route_from_database(

                    db=db,

                    user_id=user_id,

                    route_id=route_id,
                )
            )

        if not route:
            return None

        steps = route["steps"]

        geometry = route.get(
            "geometry",
            [],
        )

        destination_lat = route.get(
            "destination_lat"
        )

        destination_lng = route.get(
            "destination_lng"
        )

        distance_to_destination = None

        if (
            destination_lat is not None
            and destination_lng is not None
        ):

            distance_to_destination = (
                self.calculate_distance(

                    current_latitude,
                    current_longitude,

                    destination_lat,
                    destination_lng,
                )
            )


        # ----------------------------------------------------
        # ARRIVAL DETECTION
        # ----------------------------------------------------

        if (
            distance_to_destination is not None
            and distance_to_destination <= 20
        ):

            route[
                "navigation_status"
            ] = "ARRIVED"

            route[
                "current_step"
            ] = len(steps) - 1

            route[
                "current_instruction"
            ] = "Destination reached."

            db_route = (
                db.query(NavigationRoute)
                .filter(
                    NavigationRoute.route_id
                    == route_id,

                    NavigationRoute.user_id
                    == user_id,
                )
                .first()
            )

            if db_route:

                db_route.navigation_status = (
                    "ARRIVED"
                )

                db_route.current_step = (
                    len(steps) - 1
                )

                db_route.current_instruction = (
                    "Destination reached."
                )

                db_route.completed_at = (
                    datetime.now(timezone.utc)
                )

                db.commit()

            return {

                "route_id": route_id,

                "navigation_status": "ARRIVED",

                "current_step": (
                    len(steps) - 1
                ),

                "current_instruction": (
                    "Destination reached."
                ),

                "remaining_distance_m": 0.0,

                "off_route": False,

                "rerouting_required": False,

                "voice_instruction": (
                    "You have reached your destination."
                ),

                "rerouted": False,

                "previous_route_id": (
                    route.get(
                        "previous_route_id"
                    )
                ),

                "total_distance_m": route[
                    "total_distance_m"
                ],

                "estimated_time_minutes": route[
                    "estimated_time_minutes"
                ],
            }


        # ----------------------------------------------------
        # MOCK ROUTE FALLBACK
        # ----------------------------------------------------

        if not geometry:

            fallback_step = (
                current_step
                if current_step is not None
                else route.get(
                    "current_step",
                    0,
                )
            )

            fallback_step = max(
                0,
                min(
                    fallback_step,
                    len(steps) - 1,
                ),
            )

            step = steps[
                fallback_step
            ]

            remaining_distance = sum(

                item.distance_m

                for item in steps[
                    fallback_step:
                ]
            )

            route[
                "current_step"
            ] = fallback_step

            route[
                "current_instruction"
            ] = step.instruction

            return {

                "route_id": route_id,

                "navigation_status": "ACTIVE",

                "current_step": fallback_step,

                "current_instruction": (
                    step.instruction
                ),

                "remaining_distance_m": round(
                    remaining_distance,
                    2,
                ),

                "off_route": False,

                "rerouting_required": False,

                "voice_instruction": (
                    step.voice_instruction
                ),

                "rerouted": False,

                "previous_route_id": None,

                "total_distance_m": route[
                    "total_distance_m"
                ],

                "estimated_time_minutes": route[
                    "estimated_time_minutes"
                ],
            }


        # ----------------------------------------------------
        # FIND CURRENT GPS POSITION
        # ----------------------------------------------------

        nearest = (
            self.find_nearest_geometry_point(

                geometry=geometry,

                current_latitude=(
                    current_latitude
                ),

                current_longitude=(
                    current_longitude
                ),
            )
        )

        geometry_index = nearest[
            "index"
        ]

        distance_from_route = nearest[
            "distance_m"
        ]


        # ----------------------------------------------------
        # AUTOMATIC STEP DETECTION
        # ----------------------------------------------------

        detected_step = (
            self.determine_current_step(

                route=route,

                geometry_index=geometry_index,
            )
        )

        detected_step = max(

            0,

            min(
                detected_step,
                len(steps) - 1,
            ),
        )

        current_route_step = steps[
            detected_step
        ]


        # ----------------------------------------------------
        # REMAINING DISTANCE
        # ----------------------------------------------------

        remaining_distance = (
            self.calculate_geometry_remaining_distance(

                geometry=geometry,

                start_index=geometry_index,
            )
        )


        # ----------------------------------------------------
        # OFF-ROUTE DETECTION
        # ----------------------------------------------------

        off_route_threshold_m = 40.0

        off_route = (
            distance_from_route
            > off_route_threshold_m
        )


        # ----------------------------------------------------
        # UPDATE MEMORY STATE
        # ----------------------------------------------------

        route[
            "current_step"
        ] = detected_step

        route[
            "current_instruction"
        ] = current_route_step.instruction

        route[
            "navigation_status"
        ] = (
            "OFF_ROUTE"
            if off_route
            else "ACTIVE"
        )


        # ----------------------------------------------------
        # SAVE PROGRESS TO DATABASE
        # ----------------------------------------------------

        db_route = (
            db.query(NavigationRoute)
            .filter(
                NavigationRoute.route_id
                == route_id,

                NavigationRoute.user_id
                == user_id,
            )
            .first()
        )

        if db_route:

            db_route.current_step = (
                detected_step
            )

            db_route.current_instruction = (
                current_route_step.instruction
            )

            db_route.navigation_status = (
                "OFF_ROUTE"
                if off_route
                else "ACTIVE"
            )

            db.commit()


        # ----------------------------------------------------
        # AUTOMATIC REROUTING
        # ----------------------------------------------------

        if off_route:

            old_route_id = route_id

            try:

                new_route = self.reroute(

                    db=db,

                    user_id=user_id,

                    old_route_id=old_route_id,

                    current_latitude=(
                        current_latitude
                    ),

                    current_longitude=(
                        current_longitude
                    ),
                )

                if new_route:

                    new_first_step = (
                        new_route["steps"][0]
                    )

                    return {

                        "route_id": new_route[
                            "route_id"
                        ],

                        "navigation_status": (
                            "ACTIVE"
                        ),

                        "current_step": 0,

                        "current_instruction": (
                            new_first_step.instruction
                        ),

                        "remaining_distance_m": (
                            new_route[
                                "total_distance_m"
                            ]
                        ),

                        "off_route": False,

                        "rerouting_required": False,

                        "voice_instruction": (
                            "Route updated. "
                            + new_first_step.voice_instruction
                        ),

                        "rerouted": True,

                        "previous_route_id": (
                            old_route_id
                        ),

                        "total_distance_m": (
                            new_route[
                                "total_distance_m"
                            ]
                        ),

                        "estimated_time_minutes": (
                            new_route[
                                "estimated_time_minutes"
                            ]
                        ),
                    }

            except Exception:

                return {

                    "route_id": route_id,

                    "navigation_status": (
                        "OFF_ROUTE"
                    ),

                    "current_step": detected_step,

                    "current_instruction": (
                        current_route_step.instruction
                    ),

                    "remaining_distance_m": (
                        remaining_distance
                    ),

                    "off_route": True,

                    "rerouting_required": True,

                    "voice_instruction": (
                        "You are off the planned route. "
                        "Automatic rerouting failed."
                    ),

                    "rerouted": False,

                    "previous_route_id": None,

                    "total_distance_m": route[
                        "total_distance_m"
                    ],

                    "estimated_time_minutes": route[
                        "estimated_time_minutes"
                    ],
                }


        # ----------------------------------------------------
        # NORMAL ACTIVE ROUTE RESPONSE
        # ----------------------------------------------------

        return {

            "route_id": route_id,

            "navigation_status": "ACTIVE",

            "current_step": detected_step,

            "current_instruction": (
                current_route_step.instruction
            ),

            "remaining_distance_m": (
                remaining_distance
            ),

            "off_route": False,

            "rerouting_required": False,

            "voice_instruction": (
                current_route_step.voice_instruction
            ),

            "rerouted": False,

            "previous_route_id": (
                route.get(
                    "previous_route_id"
                )
            ),

            "total_distance_m": route[
                "total_distance_m"
            ],

            "estimated_time_minutes": route[
                "estimated_time_minutes"
            ],
        }


navigation_service = NavigationService()