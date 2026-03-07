from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class ReminderType(str, enum.Enum):
    medication = "medication"
    doctor = "doctor"
    therapy = "therapy"
    other = "other"

class RecurType(str, enum.Enum):
    none = "none"          # Tek seferlik
    daily = "daily"        # Her gün
    weekly = "weekly"      # Her hafta
    custom = "custom"      # Belirli günler

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    reminder_type = Column(Enum(ReminderType), default=ReminderType.other)
    remind_at = Column(DateTime, nullable=False)       # İlk/sonraki bildirim zamanı
    recur_type = Column(Enum(RecurType), default=RecurType.none)
    recur_days = Column(String(20), nullable=True)     # "0,2,4" = Pzt, Çar, Cum
    recur_time = Column(String(5), nullable=True)      # "09:00"
    is_sent = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    child = relationship("Child", back_populates="reminders")