"""
AutiCare Human Review Schemas
HITL onay mekanizması için Pydantic şemaları.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HumanReviewCreate(BaseModel):
    """Yeni onay kaydı oluşturma"""
    workflow_id: str
    child_id: int
    task_type: str
    ai_output: str
    confidence_score: Optional[float] = None


class HumanReviewUpdate(BaseModel):
    """Onay durumunu güncelleme (terapist/ebeveyn tarafından)"""
    status: str = Field(..., pattern="^(approved|rejected|modified)$")
    reviewer_notes: Optional[str] = None
    modified_output: Optional[str] = None


class HumanReviewResponse(BaseModel):
    """Onay kaydı yanıtı"""
    id: int
    workflow_id: str
    child_id: int
    reviewer_id: Optional[int] = None
    task_type: str
    ai_output: str
    confidence_score: Optional[float] = None
    status: str
    reviewer_notes: Optional[str] = None
    modified_output: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
