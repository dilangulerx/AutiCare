from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.database import get_db
from app.models.daily_log import DailyLog
from app.models.child import Child
from app.schemas.daily_log import DailyLogCreate, DailyLogUpdate, DailyLogResponse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/logs", tags=["Daily Logs"])

def verify_child_owner(child_id: int, db: Session, current_user):
    child = db.query(Child).filter(Child.id == child_id, Child.parent_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Çocuk bulunamadı")
    return child

@router.post("", response_model=DailyLogResponse)
def create_log(data: DailyLogCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    verify_child_owner(data.child_id, db, current_user)
    log = DailyLog(**data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@router.get("/child/{child_id}", response_model=List[DailyLogResponse])
def get_logs(child_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    verify_child_owner(child_id, db, current_user)
    return db.query(DailyLog).filter(DailyLog.child_id == child_id).order_by(DailyLog.date.desc()).all()

@router.get("/child/{child_id}/date/{log_date}", response_model=DailyLogResponse)
def get_log_by_date(child_id: int, log_date: date, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    verify_child_owner(child_id, db, current_user)
    log = db.query(DailyLog).filter(DailyLog.child_id == child_id, DailyLog.date == log_date).first()
    if not log:
        raise HTTPException(status_code=404, detail="Bu tarihe ait kayıt bulunamadı")
    return log

@router.put("/{log_id}", response_model=DailyLogResponse)
def update_log(log_id: int, data: DailyLogUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    verify_child_owner(log.child_id, db, current_user)
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(log, key, value)
    db.commit()
    db.refresh(log)
    return log

@router.delete("/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    verify_child_owner(log.child_id, db, current_user)
    db.delete(log)
    db.commit()
    return {"message": "Kayıt silindi"}