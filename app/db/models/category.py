import uuid

from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class Category(Base):
    __tablename__ = 'categories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Relationships
    journal_entries = relationship('JournalEntryCategory', back_populates='category' , cascade="all, delete-orphan")
    user = relationship('User', back_populates='categories')

    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='uix_name_user_id'),
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, user_id={self.user_id})>"
