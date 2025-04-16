from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class JournalEntryCategory(Base):
    __tablename__ = 'journal_entry_categories'

    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey('journal_entries.id'), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey('categories.id'), primary_key=True)

    # Relationships
    journal_entry = relationship('JournalEntry', back_populates='journal_entry_categories')
    category = relationship('Category', back_populates='journal_entries')
