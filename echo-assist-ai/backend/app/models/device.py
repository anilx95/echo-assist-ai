from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Device(Base):
    """Represents a physical ECHO-CANE smart cane paired to a user."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    device_name: Mapped[str] = mapped_column(String(120), default="ECHO-CANE")
    firmware_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    connection_status: Mapped[str] = mapped_column(String(20), default="disconnected")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="devices")
    sensor_readings = relationship(
        "SensorReading", back_populates="device", cascade="all, delete-orphan"
    )
