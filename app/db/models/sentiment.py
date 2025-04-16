import uuid
import pendulum

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.mood import Mood


class SentimentScore(Base):
    __tablename__ = 'sentiment_scores'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_id = Column(UUID(as_uuid=True), ForeignKey('journal_entries.id'), unique=True, nullable=False)
    score = Column(Float, nullable=False)
    magnitude = Column(Float, nullable=False)
    mood = Column(Enum(Mood), default=Mood.NEUTRAL)
    calculation = Column(JSON, nullable=False)
    positive_words = Column(String, nullable=False)
    negative_words = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: pendulum.now("UTC"), nullable=False)

    journal_entry = relationship('JournalEntry', back_populates='sentiment', uselist=False)

    def __repr__(self):
        return f"<SentimentScore(id={self.id}, journal_id={self.journal_id}, score={self.score})>"
