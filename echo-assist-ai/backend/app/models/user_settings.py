from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserSettings(Base):
    """Per-user app preferences (accessibility, alerts, language)."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    language: Mapped[str] = mapped_column(String(10), default="en")
    voice_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    vibration_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    high_contrast_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    large_text_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    fall_detection_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    fall_detection_countdown_seconds: Mapped[int] = mapped_column(Integer, default=15)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="settings")
