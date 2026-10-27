import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database import Base


class NavigationRoute(Base):

    __tablename__ = "navigation_routes"


    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )


    # ========================================================
    # PUBLIC ROUTE ID
    # ========================================================

    route_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )


    # ========================================================
    # USER
    # ========================================================

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )


    # ========================================================
    # DESTINATION INFORMATION
    # ========================================================

    destination: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    # ========================================================
    # ORIGIN GPS
    # ========================================================

    origin_lat: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    origin_lng: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )


    # ========================================================
    # DESTINATION GPS
    # ========================================================

    destination_lat: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    destination_lng: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )


    # ========================================================
    # ROUTE METRICS
    # ========================================================

    total_distance_m: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    estimated_time_minutes: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )


    # ========================================================
    # ROUTE PROGRESS
    # ========================================================

    current_step: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    current_instruction: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


    # ========================================================
    # ROUTE STATUS
    # ========================================================

    navigation_status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        nullable=False,
        index=True,
    )


    # ========================================================
    # ROUTING PROVIDER
    # ========================================================

    provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    profile: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )


    # ========================================================
    # ROUTE DATA
    # ========================================================

    geometry: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    steps: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    provider_steps: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )


    # ========================================================
    # REROUTING RELATION
    # ========================================================

    previous_route_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )

    replaced_by_route_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )


    # ========================================================
    # FLAGS
    # ========================================================

    mock_mode: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    rerouted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )


    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


    # ========================================================
    # RELATIONSHIP
    # ========================================================

    user = relationship(
        "User",
    )