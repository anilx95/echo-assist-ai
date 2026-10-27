import httpx

from app.core.config import settings


class RoutingService:

    BASE_URL = (
        "https://api.openrouteservice.org"
    )


    def __init__(self):

        self.api_key = settings.MAPS_API_KEY


    # ========================================================
    # REAL WALKING ROUTE
    # ========================================================

    def get_walking_route(
        self,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
    ):

        if not self.api_key:

            raise ValueError(
                "Routing API key is not configured."
            )


        url = (
            f"{self.BASE_URL}"
            "/v2/directions/"
            "foot-walking/geojson"
        )


        headers = {

            "Authorization": self.api_key,

            "Content-Type": "application/json",

            "Accept": "application/geo+json",
        }


        # IMPORTANT:
        # ORS coordinate order is:
        #
        # [longitude, latitude]
        #
        # NOT:
        #
        # [latitude, longitude]

        payload = {

            "coordinates": [

                [
                    origin_lng,
                    origin_lat,
                ],

                [
                    destination_lng,
                    destination_lat,
                ],
            ],

            "instructions": True,

            "language": "en",

            "units": "m",
        }


        try:

            with httpx.Client(
                timeout=30.0
            ) as client:

                response = client.post(
                    url,
                    headers=headers,
                    json=payload,
                )


            response.raise_for_status()

            data = response.json()


        except httpx.TimeoutException:

            raise RuntimeError(
                "Routing service request timed out."
            )


        except httpx.HTTPStatusError as exc:

            error_text = (
                exc.response.text
            )

            raise RuntimeError(
                f"Routing API error: "
                f"{exc.response.status_code} "
                f"{error_text}"
            )


        except httpx.RequestError as exc:

            raise RuntimeError(
                f"Could not connect to routing service: "
                f"{str(exc)}"
            )


        # ====================================================
        # VALIDATE RESPONSE
        # ====================================================

        features = data.get(
            "features",
            []
        )


        if not features:

            raise RuntimeError(
                "Routing service returned no route."
            )


        feature = features[0]

        properties = feature.get(
            "properties",
            {}
        )

        summary = properties.get(
            "summary",
            {}
        )

        segments = properties.get(
            "segments",
            []
        )

        geometry = feature.get(
            "geometry",
            {}
        )


        # ====================================================
        # EXTRACT ROUTE STEPS
        # ====================================================

        route_steps = []

        step_number = 1


        for segment in segments:

            for step in segment.get(
                "steps",
                []
            ):

                instruction = step.get(
                    "instruction",
                    "Continue",
                )

                distance = float(
                    step.get(
                        "distance",
                        0,
                    )
                )

                duration = float(
                    step.get(
                        "duration",
                        0,
                    )
                )


                route_steps.append({

                    "step_number": (
                        step_number
                    ),

                    "instruction": (
                        instruction
                    ),

                    "distance_m": round(
                        distance,
                        2,
                    ),

                    "duration_seconds": round(
                        duration,
                        2,
                    ),

                    "type": step.get(
                        "type"
                    ),

                    "way_points": step.get(
                        "way_points",
                        [],
                    ),
                })


                step_number += 1


        return {

            "total_distance_m": round(
                float(
                    summary.get(
                        "distance",
                        0,
                    )
                ),
                2,
            ),

            "total_duration_seconds": round(
                float(
                    summary.get(
                        "duration",
                        0,
                    )
                ),
                2,
            ),

            "estimated_time_minutes": round(
                float(
                    summary.get(
                        "duration",
                        0,
                    )
                ) / 60,
                1,
            ),

            "steps": route_steps,

            "geometry": geometry.get(
                "coordinates",
                [],
            ),

            "provider": (
                "openrouteservice"
            ),

            "profile": (
                "foot-walking"
            ),
        }


routing_service = RoutingService()