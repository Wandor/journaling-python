import uuid
import pendulum

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

from app.db.models.time_of_day import TimeOfDay

class AnalyticsData(Base):
    __tablename__ = "analytics_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_id = Column(UUID(as_uuid=True), ForeignKey('journal_entries.id', ondelete="CASCADE"), unique=True)
    word_count = Column(Integer, nullable=False)
    character_count = Column(Integer, nullable=False)
    sentence_count = Column(Integer, nullable=False)
    reading_time = Column(Integer, nullable=False)
    average_sentence_length = Column(Float, nullable=False)
    tags_count = Column(Integer, nullable=False)
    categories_count = Column(Integer, nullable=False)
    entry_date = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), nullable=False)
    time_of_day = Column(Enum(TimeOfDay), default=TimeOfDay.MORNING)

    journal_entry = relationship("JournalEntry", back_populates="analytics")
