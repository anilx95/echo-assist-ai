from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmergencyEvent(Base):
    """
    Stores emergency events created by:
    - automatic fall detection
    - manual SOS
    - voice emergency command
    """

    __tablename__ = "emergency_events"


    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
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
    # EMERGENCY TYPE
    # ========================================================

    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )


    # ========================================================
    # GPS LOCATION
    # ========================================================

    # GPS may not be immediately available when an automatic
    # fall is detected, so these fields must allow NULL values.

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )


    # ========================================================
    # STATUS
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )


    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


    # ========================================================
    # RELATIONSHIP
    # ========================================================

    user = relationship(
        "User",
        back_populates="emergency_events",
    )