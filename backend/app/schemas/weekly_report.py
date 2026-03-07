from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

class WeeklyReportResponse(BaseModel):
    id: int
    child_id: int
    week_start_date: date
    report_text: Optional[str] = None
    key_insights: Optional[dict] = None
    recommendations: Optional[List[str]] = None
    generated_at: datetime

    class Config:
        from_attributes = True