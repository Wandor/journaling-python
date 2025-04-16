from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class JournalEntryTag(Base):
    __tablename__ = 'journal_entry_tags'

    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey('journal_entries.id'), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True)

    # Relationships
    journal_entry = relationship('JournalEntry', back_populates='journal_entry_tags')
    tag = relationship('Tag', back_populates='journal_entries')
