from openai import OpenAI
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.models.daily_log import DailyLog
from app.models.weekly_report import WeeklyReport
import os
import json

def get_week_logs(db: Session, child_id: int, week_start: date):
    week_end = week_start + timedelta(days=6)
    return db.query(DailyLog).filter(
        DailyLog.child_id == child_id,
        DailyLog.date >= week_start,
        DailyLog.date <= week_end
    ).all()

def calculate_averages(logs):
    if not logs:
        return {}
    fields = ["eye_contact", "aggression_level", "communication_score", "sleep_hours"]
    averages = {}
    for field in fields:
        values = [getattr(log, field) for log in logs if getattr(log, field) is not None]
        if values:
            averages[field] = round(sum(values) / len(values), 2)
    return averages

def generate_weekly_report(db: Session, child_id: int, child_name: str, week_start: date):
    logs = get_week_logs(db, child_id, week_start)
    if not logs:
        return None

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    averages = calculate_averages(logs)

    logs_text = ""
    for log in logs:
        logs_text += f"\n- {log.date}: Göz teması={log.eye_contact}, Agresyon={log.aggression_level}, İletişim={log.communication_score}, Uyku={log.sleep_hours} saat"
        if log.notes:
            logs_text += f", Not: {log.notes}"

    prompt = f"""Sen otizmli çocukların gelişimini takip eden, ebeveynlere destek olan bir asistansın.
Ebeveynlere yargılamayan, destekleyici ve umut verici bir tonla davranış analizi sunarsın.
Kesinlikle tıbbi teşhis koymazsın, "ASD level", "klinik" gibi terimler kullanmazsın.

Çocuk adı: {child_name}
Hafta: {week_start} - {week_start + timedelta(days=6)}

Haftalık kayıtlar:{logs_text}

Ortalamalar:
- Göz teması: {averages.get('eye_contact', 'veri yok')} / 5
- Agresyon: {averages.get('aggression_level', 'veri yok')} / 5
- İletişim: {averages.get('communication_score', 'veri yok')} / 5
- Uyku: {averages.get('sleep_hours', 'veri yok')} saat

Sadece şu JSON formatında yanıt ver:
{{
    "report_text": "3-4 paragraf destekleyici rapor",
    "key_insights": {{
        "en_iyi_gun": "tarih ve neden",
        "gelisim_alani": "en çok gelişim gösteren alan",
        "dikkat_alani": "dikkat edilmesi gereken alan"
    }},
    "recommendations": ["öneri 1", "öneri 2", "öneri 3"]
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    data = json.loads(content.strip())

    report = WeeklyReport(
        child_id=child_id,
        week_start_date=week_start,
        report_text=data.get("report_text"),
        key_insights=data.get("key_insights"),
        recommendations=data.get("recommendations")
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report