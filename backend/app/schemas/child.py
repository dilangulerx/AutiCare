from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class ChildCreate(BaseModel):
    name: str
    birth_date: Optional[date] = None
    notes: Optional[str] = None

class ChildUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[date] = None
    notes: Optional[str] = None

class ChildResponse(BaseModel):
    id: int
    parent_id: int
    name: str
    birth_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True