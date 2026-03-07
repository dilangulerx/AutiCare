from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.reminder import ReminderType, RecurType

class ReminderCreate(BaseModel):
    child_id: int
    title: str
    description: Optional[str] = None
    reminder_type: ReminderType = ReminderType.other
    remind_at: datetime
    recur_type: RecurType = RecurType.none
    recur_days: Optional[str] = None   # "0,2,4" → Pzt, Çar, Cum
    recur_time: Optional[str] = None   # "09:00"

class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    remind_at: Optional[datetime] = None
    recur_type: Optional[RecurType] = None
    recur_days: Optional[str] = None
    recur_time: Optional[str] = None
    is_active: Optional[bool] = None

class ReminderResponse(BaseModel):
    id: int
    child_id: int
    title: str
    description: Optional[str] = None
    reminder_type: ReminderType
    remind_at: datetime
    recur_type: RecurType
    recur_days: Optional[str] = None
    recur_time: Optional[str] = None
    is_sent: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True