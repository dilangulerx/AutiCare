from sqlalchemy import Column, Integer, Date, Text, ForeignKey, DateTime, Float
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
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    child = relationship("Child", back_populates="daily_logs")