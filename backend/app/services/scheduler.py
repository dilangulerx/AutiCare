from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.reminder import Reminder, RecurType
from app.models.child import Child
from app.models.user import User
from app.services.email import send_reminder_email
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def get_next_occurrence(reminder: Reminder, now: datetime):
    """Tekrarlayan hatırlatıcı için sonraki zamanı hesapla"""
    hour, minute = map(int, reminder.recur_time.split(":"))

    if reminder.recur_type == RecurType.daily:
        next_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_dt <= now:
            next_dt += timedelta(days=1)
        return next_dt

    elif reminder.recur_type == RecurType.weekly:
        original_weekday = reminder.remind_at.weekday()
        next_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = original_weekday - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return next_dt + timedelta(days=days_ahead)

    elif reminder.recur_type == RecurType.custom and reminder.recur_days:
        allowed_days = [int(d) for d in reminder.recur_days.split(",")]
        next_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_dt <= now:
            next_dt += timedelta(days=1)
        for _ in range(7):
            if next_dt.weekday() in allowed_days:
                return next_dt
            next_dt += timedelta(days=1)

    return None

def check_and_send_reminders():
    db: Session = SessionLocal()
    try:
        now = datetime.now()
        due_reminders = db.query(Reminder).filter(
            Reminder.remind_at <= now,
            Reminder.is_active == True,
            Reminder.is_sent == False
        ).all()

        for reminder in due_reminders:
            try:
                child = db.query(Child).filter(Child.id == reminder.child_id).first()
                if not child:
                    continue
                user = db.query(User).filter(User.id == child.parent_id).first()
                if not user:
                    continue

                send_reminder_email(
                    to_email=user.email,
                    child_name=child.name,
                    title=reminder.title,
                    description=reminder.description,
                    reminder_type=reminder.reminder_type
                )

                if reminder.recur_type != RecurType.none:
                    next_time = get_next_occurrence(reminder, now)
                    if next_time:
                        reminder.remind_at = next_time
                        reminder.is_sent = False
                else:
                    reminder.is_sent = True

                db.commit()
                logger.info(f"Reminder sent: {reminder.title} → {user.email}")

            except Exception as e:
                logger.error(f"Reminder error {reminder.id}: {e}")

    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(
        check_and_send_reminders,
        IntervalTrigger(minutes=1),
        id="reminder_checker",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started!")

def stop_scheduler():
    scheduler.shutdown()