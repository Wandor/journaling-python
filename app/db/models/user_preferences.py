import uuid
import pendulum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class UserPreferences(Base):
    __tablename__ = 'user_preferences'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True)
    two_factor_enabled = Column(Boolean, default=False)
    enable_notifications = Column(Boolean, default=True)
    auto_tag = Column(Boolean, default=True)
    auto_categorize = Column(Boolean, default=True)
    summarize = Column(Boolean, default=True)
    reminder_time = Column(DateTime, nullable=True)
    language = Column(String, default="en")
    time_zone = Column(String, default="UTC")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: pendulum.now("UTC"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: pendulum.now("UTC"),
        onupdate=lambda: pendulum.now("UTC"),
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences(id={self.id}, user_id={self.user_id}, two_factor_enabled={self.two_factor_enabled})>"
