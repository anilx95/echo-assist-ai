from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SensorReading(Base):
    """A single packet of sensor data received from the ESP32 smart cane."""

    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)

    ultrasonic_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    tof_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    accel_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    accel_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    accel_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    gyro_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    gyro_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    gyro_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    sos_pressed: Mapped[bool] = mapped_column(Boolean, default=False)
    battery_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    device_timestamp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    device = relationship("Device", back_populates="sensor_readings")
