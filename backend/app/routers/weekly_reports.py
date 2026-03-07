from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.database import get_db
from app.models.weekly_report import WeeklyReport
from app.models.child import Child
from app.schemas.weekly_report import WeeklyReportResponse
from app.services.ai_report import generate_weekly_report
from app.routers.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Weekly Reports"])

def verify_child_owner(child_id: int, db: Session, current_user):
    child = db.query(Child).filter(Child.id == child_id, Child.parent_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Çocuk bulunamadı")
    return child

@router.post("/generate/{child_id}", response_model=WeeklyReportResponse)
def generate_report(child_id: int, week_start: date, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    child = verify_child_owner(child_id, db, current_user)
    report = generate_weekly_report(db, child_id, child.name, week_start)
    if not report:
        raise HTTPException(status_code=400, detail="Bu haftaya ait kayıt bulunamadı")
    return report

@router.get("/child/{child_id}", response_model=List[WeeklyReportResponse])
def get_reports(child_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    verify_child_owner(child_id, db, current_user)
    return db.query(WeeklyReport).filter(WeeklyReport.child_id == child_id).order_by(WeeklyReport.generated_at.desc()).all()

@router.get("/{report_id}", response_model=WeeklyReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı")
    verify_child_owner(report.child_id, db, current_user)
    return report