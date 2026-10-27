from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings

from app.models.user import User

from app.schemas.navigation import (
    NavigationProgressRequest,
    NavigationProgressResponse,
    RouteRequest,
    RouteResponse,
)

from app.services.auth_service import (
    get_current_user,
)

from app.services.navigation_service import (
    navigation_service,
)


router = APIRouter(
    prefix="/navigation",
    tags=["navigation"],
)


# ============================================================
# CREATE WALKING ROUTE
# ============================================================

@router.post(
    "/route",
    response_model=RouteResponse,
)
def get_route(

    payload: RouteRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    # ========================================================
    # REAL ROUTING
    # ========================================================

    if settings.MAPS_API_KEY:

        try:

            route = (
                navigation_service
                .create_real_route(

                    db=db,

                    user_id=current_user.id,

                    destination=(
                        payload.destination
                    ),

                    origin_lat=(
                        payload.origin_lat
                    ),

                    origin_lng=(
                        payload.origin_lng
                    ),

                    destination_lat=(
                        payload.destination_lat
                    ),

                    destination_lng=(
                        payload.destination_lng
                    ),
                )
            )


            return RouteResponse(
                **route
            )


        except ValueError as exc:

            raise HTTPException(
                status_code=400,
                detail=str(exc),
            )


        except RuntimeError as exc:

            raise HTTPException(
                status_code=502,
                detail=str(exc),
            )


        except Exception as exc:

            raise HTTPException(
                status_code=502,
                detail=(
                    f"Routing service error: "
                    f"{str(exc)}"
                ),
            )


    # ========================================================
    # DEVELOPMENT FALLBACK ROUTE
    # ========================================================

    route = (
        navigation_service
        .create_mock_route(

            destination=(
                payload.destination
            ),

            origin_lat=(
                payload.origin_lat
            ),

            origin_lng=(
                payload.origin_lng
            ),

            destination_lat=(
                payload.destination_lat
            ),

            destination_lng=(
                payload.destination_lng
            ),
        )
    )


    return RouteResponse(
        **route
    )


# ============================================================
# GPS-BASED NAVIGATION PROGRESS
# ============================================================

@router.post(
    "/progress",
    response_model=NavigationProgressResponse,
)
def update_navigation_progress(

    payload: NavigationProgressRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    # --------------------------------------------------------
    # UPDATE ROUTE USING CURRENT GPS LOCATION
    # --------------------------------------------------------

    result = (
        navigation_service
        .update_progress(

            route_id=(
                payload.route_id
            ),

            current_latitude=(
                payload.current_latitude
            ),

            current_longitude=(
                payload.current_longitude
            ),

            # These arguments will be used by the
            # persistent navigation implementation.

            db=db,

            user_id=current_user.id,
        )
    )


    # --------------------------------------------------------
    # ROUTE NOT FOUND
    # --------------------------------------------------------

    if result is None:

        raise HTTPException(

            status_code=404,

            detail=(
                "Navigation route not found. "
                "Create a new route before sending "
                "GPS progress updates."
            ),
        )


    # --------------------------------------------------------
    # RETURN NAVIGATION STATUS
    # --------------------------------------------------------

    return NavigationProgressResponse(
        **result
    )