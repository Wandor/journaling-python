import uuid
import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

class Session(Base):
    __tablename__ = 'sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    otp_value = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    refresh_token = Column(String, nullable=False)
    refresh_token_expiry = Column(DateTime, default=datetime.datetime.utcnow)
    otp_verified = Column(Boolean, default=True)
    session_start = Column(DateTime, default=datetime.datetime.utcnow)
    session_end = Column(DateTime, nullable=True)
    session_status = Column(Boolean, default=True)
    clustered_id = Column(Integer, autoincrement=True)
    ip_address = Column(String, default="Unknown")
    device_id = Column(String, nullable=True)

    user = relationship('User', back_populates='sessions')

    __table_args__ = (
        Index('ix_sessions_user_id', 'user_id'),
    )

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, session_start={self.session_start})>"
