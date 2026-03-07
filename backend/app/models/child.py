from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    birth_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parent = relationship("User", back_populates="children")
    daily_logs = relationship("DailyLog", back_populates="child", cascade="all, delete-orphan")
    weekly_reports = relationship("WeeklyReport", back_populates="child", cascade="all, delete-orphan")

    reminders = relationship("Reminder", back_populates="child", cascade="all, delete-orphan")