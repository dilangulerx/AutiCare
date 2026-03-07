from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.reminder import Reminder
from app.models.child import Child
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/reminders", tags=["Reminders"])

def verify_child_owner(child_id: int, db: Session, current_user):
    child = db.query(Child).filter(Child.id == child_id, Child.parent_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Çocuk bulunamadı")
    return child

@router.post("", response_model=ReminderResponse)
def create_reminder(data: ReminderCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    verify_child_owner(data.child_id, db, current_user)
    reminder = Reminder(**data.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder

@router.get("/child/{child_id}", response_model=List[ReminderResponse])
def get_reminders(child_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    verify_child_owner(child_id, db, current_user)
    return db.query(Reminder).filter(Reminder.child_id == child_id).order_by(Reminder.remind_at).all()

@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(reminder_id: int, data: ReminderUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Hatırlatıcı bulunamadı")
    verify_child_owner(reminder.child_id, db, current_user)
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(reminder, key, value)
    db.commit()
    db.refresh(reminder)
    return reminder

@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Hatırlatıcı bulunamadı")
    verify_child_owner(reminder.child_id, db, current_user)
    db.delete(reminder)
    db.commit()
    return {"message": "Hatırlatıcı silindi"}