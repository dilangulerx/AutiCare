"""
AutiCare Human Review Model
İnsan-döngüde (HITL) onay kayıtları için veritabanı modeli.

NEDEN?
AI tarafından üretilen kritik çıktılar (terapi önerileri, anomali raporları)
bir insan uzmanın gözden geçirmesi için saklanmalı. Bu model, her review
sürecini takip eder: kim, ne zaman, hangi çıktıyı, nasıl değerlendirdi.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class HumanReview(Base):
    """
    İnsan Onay Kaydı
    
    workflow_id: LangGraph iş akışı ID'si
    child_id: İlgili çocuğun ID'si
    reviewer_id: Onaylayan kullanıcı (terapist/ebeveyn) ID'si
    task_type: Görev türü (report, anomaly, vb.)
    ai_output: AI'ın ürettiği orijinal çıktı
    confidence_score: AI güven skoru (0-1)
    status: pending | approved | rejected | modified
    reviewer_notes: Uzman notları
    modified_output: Düzenlenen çıktı (varsa)
    """
    __tablename__ = "human_reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    task_type = Column(String(50), nullable=False)
    ai_output = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    reviewer_notes = Column(Text, nullable=True)
    modified_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    
    # İlişkiler
    child = relationship("Child", backref="human_reviews")
