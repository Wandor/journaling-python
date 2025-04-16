import pendulum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

def default_expiry():
    return pendulum.now().add(days=30)

class Password(Base):
    __tablename__ = 'passwords'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    password = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    password_expiry = Column(DateTime, default=default_expiry, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), nullable=False)
    clustered_id = Column(Integer, autoincrement=True)

    user = relationship('User', back_populates='passwords')

    def __repr__(self):
        return f"<Password(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
