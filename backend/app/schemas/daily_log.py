from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

class DailyLogCreate(BaseModel):
    child_id: int
    date: date
    eye_contact: Optional[int] = Field(None, ge=1, le=5)
    aggression_level: Optional[int] = Field(None, ge=1, le=5)
    communication_score: Optional[int] = Field(None, ge=1, le=5)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    notes: Optional[str] = None

class DailyLogUpdate(BaseModel):
    eye_contact: Optional[int] = Field(None, ge=1, le=5)
    aggression_level: Optional[int] = Field(None, ge=1, le=5)
    communication_score: Optional[int] = Field(None, ge=1, le=5)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    notes: Optional[str] = None

class DailyLogResponse(BaseModel):
    id: int
    child_id: int
    date: date
    eye_contact: Optional[int] = None
    aggression_level: Optional[int] = None
    communication_score: Optional[int] = None
    sleep_hours: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True