from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.daily_log import DailyLog
from app.models.child import Child
from app.services.crew_report import generate_chat_response

router = APIRouter(prefix="/ai", tags=["AI"])

class ChatRequest(BaseModel):
    message: str

@router.post("/chat/{child_id}")
def chat(child_id: int, request: ChatRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Çocuk bulunamadı")

    logs = db.query(DailyLog).filter(DailyLog.child_id == child_id).order_by(DailyLog.date.desc()).limit(7).all()

    logs_data = [{
        "date": str(log.date),
        "eye_contact": log.eye_contact,
        "communication_score": log.communication_score,
        "aggression_level": log.aggression_level,
        "sleep_hours": log.sleep_hours,
        "notes": log.notes
    } for log in logs]

    try:
        response = generate_chat_response(child.name, request.message, logs_data)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomaly/{child_id}")
def check_anomaly(child_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Çocuk bulunamadı")

    logs = db.query(DailyLog).filter(DailyLog.child_id == child_id).order_by(DailyLog.date.desc()).limit(7).all()

    if len(logs) < 2:
        return {"has_anomaly": False, "message": "Yeterli veri yok"}

    logs_data = [{
        "date": str(log.date),
        "eye_contact": log.eye_contact,
        "communication_score": log.communication_score,
        "aggression_level": log.aggression_level,
        "sleep_hours": log.sleep_hours,
        "notes": log.notes
    } for log in logs]

    from app.services.crew_report import detect_anomalies
    result = detect_anomalies(child.name, logs_data)
    return result