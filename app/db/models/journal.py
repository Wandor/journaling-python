import uuid
import pendulum

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class JournalEntry(Base):
    __tablename__ = 'journal_entries'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=True)
    content = Column(String, nullable=False)
    summary = Column(String, nullable=True)
    entry_date = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Relationships
    user = relationship('User', back_populates='journal_entries', single_parent=True, cascade="all, delete-orphan")
    journal_entry_tags = relationship("JournalEntryTag", back_populates="journal_entry", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="journal_entry_tags", viewonly=True)
    journal_entry_categories = relationship("JournalEntryCategory", back_populates="journal_entry", cascade="all, delete-orphan")
    categories = relationship("Category", secondary="journal_entry_categories", viewonly=True)
    sentiment = relationship('SentimentScore', back_populates='journal_entry', uselist=False, cascade="all, delete-orphan")
    analytics = relationship('AnalyticsData', back_populates='journal_entry', uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "entry_date": self.entry_date.isoformat(),
            "categories": [category.to_dict() for category in self.categories],
            "tags": [tag.to_dict() for tag in self.tags],
        }