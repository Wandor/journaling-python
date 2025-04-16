import uuid

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base import Base

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    user = relationship('User', back_populates='tags')
    journal_entries = relationship('JournalEntryTag', back_populates='tag', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='uq_tag_name_user_id'),
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name}, user_id={self.user_id})>"
