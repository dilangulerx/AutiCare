from sqlalchemy import Column, Integer, Date, Text, ForeignKey, DateTime, Float, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    date = Column(Date, nullable=False)
    eye_contact = Column(Integer, nullable=True)
    aggression_level = Column(Integer, nullable=True)
    communication_score = Column(Integer, nullable=True)
    sleep_hours = Column(Float, nullable=True)
    sleep_start_time = Column(String(5), nullable=True)
    sleep_end_time = Column(String(5), nullable=True)
    sleep_interruptions = Column(Integer, nullable=True)
    eye_contact_frequency = Column(Integer, nullable=True)
    eye_contact_duration_seconds = Column(Float, nullable=True)
    eye_contact_context = Column(Text, nullable=True)
    aggression_frequency = Column(Integer, nullable=True)
    aggression_duration_minutes = Column(Float, nullable=True)
    aggression_trigger = Column(Text, nullable=True)
    communication_mode = Column(String(20), nullable=True)
    communication_function = Column(String(50), nullable=True)
    communication_effectiveness = Column(Integer, nullable=True)
    antecedent = Column(Text, nullable=True)
    behavior = Column(Text, nullable=True)
    consequence = Column(Text, nullable=True)
    sensory_trigger = Column(Text, nullable=True)
    gi_notes = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    child = relationship("Child", back_populates="daily_logs")