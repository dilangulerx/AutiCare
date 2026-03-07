from sqlalchemy import Column, Integer, Date, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    week_start_date = Column(Date, nullable=False)
    report_text = Column(Text, nullable=True)
    key_insights = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    child = relationship("Child", back_populates="weekly_reports")