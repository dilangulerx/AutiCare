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
    sleep_start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    sleep_end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    sleep_interruptions: Optional[int] = Field(None, ge=0, le=20)
    eye_contact_frequency: Optional[int] = Field(None, ge=0, le=500)
    eye_contact_duration_seconds: Optional[float] = Field(None, ge=0, le=3600)
    eye_contact_context: Optional[str] = None
    aggression_frequency: Optional[int] = Field(None, ge=0, le=100)
    aggression_duration_minutes: Optional[float] = Field(None, ge=0, le=1440)
    aggression_trigger: Optional[str] = None
    communication_mode: Optional[str] = Field(None, pattern=r"^(verbal|non_verbal|mixed)$")
    communication_function: Optional[str] = Field(None, max_length=50)
    communication_effectiveness: Optional[int] = Field(None, ge=1, le=5)
    antecedent: Optional[str] = None
    behavior: Optional[str] = None
    consequence: Optional[str] = None
    sensory_trigger: Optional[str] = None
    gi_notes: Optional[str] = None
    notes: Optional[str] = None

class DailyLogUpdate(BaseModel):
    eye_contact: Optional[int] = Field(None, ge=1, le=5)
    aggression_level: Optional[int] = Field(None, ge=1, le=5)
    communication_score: Optional[int] = Field(None, ge=1, le=5)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    sleep_end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    sleep_interruptions: Optional[int] = Field(None, ge=0, le=20)
    eye_contact_frequency: Optional[int] = Field(None, ge=0, le=500)
    eye_contact_duration_seconds: Optional[float] = Field(None, ge=0, le=3600)
    eye_contact_context: Optional[str] = None
    aggression_frequency: Optional[int] = Field(None, ge=0, le=100)
    aggression_duration_minutes: Optional[float] = Field(None, ge=0, le=1440)
    aggression_trigger: Optional[str] = None
    communication_mode: Optional[str] = Field(None, pattern=r"^(verbal|non_verbal|mixed)$")
    communication_function: Optional[str] = Field(None, max_length=50)
    communication_effectiveness: Optional[int] = Field(None, ge=1, le=5)
    antecedent: Optional[str] = None
    behavior: Optional[str] = None
    consequence: Optional[str] = None
    sensory_trigger: Optional[str] = None
    gi_notes: Optional[str] = None
    notes: Optional[str] = None

class DailyLogResponse(BaseModel):
    id: int
    child_id: int
    date: date
    eye_contact: Optional[int] = None
    aggression_level: Optional[int] = None
    communication_score: Optional[int] = None
    sleep_hours: Optional[float] = None
    sleep_start_time: Optional[str] = None
    sleep_end_time: Optional[str] = None
    sleep_interruptions: Optional[int] = None
    eye_contact_frequency: Optional[int] = None
    eye_contact_duration_seconds: Optional[float] = None
    eye_contact_context: Optional[str] = None
    aggression_frequency: Optional[int] = None
    aggression_duration_minutes: Optional[float] = None
    aggression_trigger: Optional[str] = None
    communication_mode: Optional[str] = None
    communication_function: Optional[str] = None
    communication_effectiveness: Optional[int] = None
    antecedent: Optional[str] = None
    behavior: Optional[str] = None
    consequence: Optional[str] = None
    sensory_trigger: Optional[str] = None
    gi_notes: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True