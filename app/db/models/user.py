import uuid
import pendulum

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.user_role import UserRole

from app.db.base import Base

class User(Base):
    __tablename__ = 'users'

    # Columns
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_name = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email_address = Column(String, unique=True, nullable=False)
    mobile_number = Column(String, nullable=False)
    access_failed_count = Column(Integer, default=0)
    otp_resend_count = Column(Integer, default=0)
    is_locked_out = Column(Boolean, default=False)
    status = Column(Boolean, default=True)
    otp_sent = Column(Boolean, default=False)
    last_password_changed_date = Column(DateTime, nullable=True)
    last_otp_resend_date = Column(DateTime, nullable=True)
    last_login_date = Column(DateTime, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), onupdate=lambda: pendulum.now("UTC"), nullable=False)

    # Relationships
    journal_entries = relationship("JournalEntry", back_populates="user")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    passwords = relationship("Password", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="user")
    categories = relationship("Category", back_populates="user")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email_address}, role={self.role})>"
