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

@router.post("/generate/{child_id}")
def generate_report(
    child_id: int,
    week_start: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.crew_report import generate_crew_report
    
    # Haftanın loglarını çek
    from datetime import datetime, timedelta
    from app.models.daily_log import DailyLog
    
    week_start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
    week_end_date = week_start_date + timedelta(days=7)
    
    logs = db.query(DailyLog).filter(
        DailyLog.child_id == child_id,
        DailyLog.date >= week_start_date,
        DailyLog.date < week_end_date
    ).all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="Bu hafta için kayıt bulunamadı")
    
    # Child bilgisini al
    from app.models.child import Child
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Çocuk bulunamadı")
    
    # Log verilerini dict'e çevir
    logs_data = [{
        "date": str(log.date),
        "eye_contact": log.eye_contact,
        "communication_score": log.communication_score,
        "aggression_level": log.aggression_level,
        "sleep_hours": log.sleep_hours,
        "notes": log.notes
    } for log in logs]
    
    # CrewAI ile rapor üret
    result = generate_crew_report(child.name, logs_data)
    
    # Veritabanına kaydet
    from app.models.weekly_report import WeeklyReport
    report = WeeklyReport(
        child_id=child_id,
        week_start_date=week_start_date,
        report_text=result["report_text"],
        key_insights={"generated_by": result["generated_by"]},
        recommendations=[]
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
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