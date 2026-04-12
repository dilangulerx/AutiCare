import asyncio
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.daily_log import DailyLog
from app.models.child import Child
from app.services.crew_report import generate_chat_response, detect_anomalies
from app.workflow import get_workflow_executor
from app.crew_manager import get_crew_manager
from app.monitoring import get_monitor, get_performance_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])

# ============================================================================
# PYDANTIC MODELLERI
# ============================================================================

class ChatRequest(BaseModel):
    """Sohbet İsteği"""
    message: str


class WorkflowRequest(BaseModel):
    """LangGraph İş Akışı İsteği"""
    task_type: str  # "report", "chat", "anomaly", "analysis"
    query: Optional[str] = None
    streaming: bool = False


class WorkflowResponse(BaseModel):
    """LangGraph İş Akışı Yanıtı"""
    success: bool
    status: str
    output: str
    analysis: Optional[dict] = None
    anomalies: Optional[List[dict]] = None
    recommendations: Optional[List[str]] = None
    execution_time: float
    error: Optional[str] = None


# ============================================================================
# KLASIK ENDPOINTS (MEVCUT UYUMLULUK İÇİN)
# ============================================================================

@router.post("/chat/{child_id}")
def chat(
    child_id: int,
    request: ChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Klasik Sohbet Endpoint (Uyumlu)
    """
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
def check_anomaly(
    child_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Klasik Anomali Tespiti Endpoint (Uyumlu)
    """
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

    result = detect_anomalies(child.name, logs_data)
    return result


# ============================================================================
# LANGGRAPH HİBRİT AI ENDPOINTS (YENİ NESIL)
# ============================================================================

@router.post("/v2/workflow/{child_id}", response_model=WorkflowResponse)
async def execute_workflow(
    child_id: int,
    request: WorkflowRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    LangGraph + CrewAI Hibrit İş Akışı Çalıştır
    
    Task Types:
    - "report": Haftalık AI raporu oluştur (Tüm ajanlar)
    - "chat": Ebeveyn sorusuna cevap ver (Conversation Agent)
    - "anomaly": Anormal davranış tespiti (Anomaly Detector)
    - "analysis": Derinlemesine davranış analizi (Behavioral Analyst)
    
    Args:
        child_id: Çocuk ID'si
        request: İş akışı isteği
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu
    
    Returns:
        WorkflowResponse: İş akışı sonuçları
    """
    
    # Çocuğu ve ebeveyn bilgilerini al
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Çocuk bulunamadı")
    
    # Günlük verileri al
    logs = db.query(DailyLog).filter(
        DailyLog.child_id == child_id
    ).order_by(DailyLog.date.desc()).limit(30).all()
    
    logs_data = [{
        "date": str(log.date),
        "eye_contact": log.eye_contact,
        "communication_score": log.communication_score,
        "aggression_level": log.aggression_level,
        "sleep_hours": log.sleep_hours,
        "behavioral_notes": log.notes,
    } for log in logs]
    
    # Monitoring başlat
    monitor = get_monitor()
    perf_tracker = get_performance_tracker()
    workflow_id = f"wf_{child_id}_{datetime.now().timestamp()}"
    
    try:
        start_time = datetime.now()
        
        # İş akışını başlat
        monitor.log_workflow_start(
            workflow_id=workflow_id,
            child_id=child_id,
            task_type=request.task_type,
            metadata={"query": request.query}
        )
        
        # Workflow executor'ı al
        executor = get_workflow_executor()
        
        # İş akışını çalıştır
        result = await executor.execute(
            child_id=child_id,
            child_name=child.name,
            parent_id=child.parent_id,
            task_type=request.task_type,
            logs_data=logs_data,
            query=request.query,
            streaming=request.streaming,
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Performansı kayıt et
        perf_tracker.record_execution_time("workflow", execution_time)
        
        # Tamamlanmayı logging et
        monitor.log_workflow_end(
            workflow_id=workflow_id,
            execution_time=execution_time,
            status=result.get("status", "completed"),
            metadata={
                "task_type": request.task_type,
                "logs_count": len(logs_data),
            }
        )
        
        logger.info(f"✓ Workflow tamamlandı: {request.task_type} ({execution_time:.2f}s)")
        
        return WorkflowResponse(
            success=result.get("success", False),
            status=result.get("status", "completed"),
            output=result.get("output", ""),
            analysis=result.get("analysis"),
            anomalies=result.get("anomalies"),
            recommendations=result.get("recommendations"),
            execution_time=execution_time,
            error=result.get("error"),
        )
    
    except Exception as e:
        logger.error(f"❌ Workflow hatası: {str(e)}", exc_info=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        perf_tracker.record_execution_time("workflow_error", execution_time)
        
        monitor.log_error("Workflow", e, {"child_id": child_id, "task_type": request.task_type})
        
        return WorkflowResponse(
            success=False,
            status="error",
            output="",
            execution_time=execution_time,
            error=str(e),
        )


@router.get("/v2/workflow/info")
def get_workflow_info():
    """
    LangGraph İş Akışı Hakkında Bilgi Al
    """
    executor = get_workflow_executor()
    crew_manager = get_crew_manager()
    monitor = get_monitor()
    
    return {
        "workflow": executor.get_workflow_info(),
        "crew": crew_manager.get_crew_info(),
        "monitoring": {
            "statistics": monitor.get_statistics(),
            "langsmith_enabled": monitor.tracking_enabled,
        },
    }


@router.get("/v2/monitoring/stats")
def get_monitoring_stats():
    """
    İzleme İstatistiklerini Al
    """
    monitor = get_monitor()
    perf_tracker = get_performance_tracker()
    
    return {
        "events": monitor.get_statistics(),
        "performance": perf_tracker.get_performance_stats(),
    }


# ============================================================================
# CREW MANAGEMENT ENDPOINTS (ADVANSEDv)
# ============================================================================

@router.post("/v2/crew/{crew_type}/{child_id}")
async def execute_crew(
    crew_type: str,
    child_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Doğrudan CrewAI Ekipini Çalıştır
    
    Crew Types:
    - "analysis": Davranış Analizi
    - "anomaly": Anomali Tespiti
    - "recommendations": Terapi Önerileri
    - "report": Haftalık Rapor
    - "chat": Sohbet
    
    Args:
        crew_type: CrewAI ekip türü
        child_id: Çocuk ID'si
        current_user: Mevcut kullanıcı
        db: Veritabanı oturumu
    
    Returns:
        Crew çalıştırma sonuçları
    """
    
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Çocuk bulunamadı")
    
    logs = db.query(DailyLog).filter(
        DailyLog.child_id == child_id
    ).order_by(DailyLog.date.desc()).limit(30).all()
    
    logs_text = "\n".join([
        f"[{log.date}] Göz İletişimi: {log.eye_contact}, "
        f"İletişim: {log.communication_score}, "
        f"Aggresyon: {log.aggression_level}, "
        f"Not: {log.notes or 'Yok'}"
        for log in logs
    ])
    
    monitor = get_monitor()
    
    try:
        manager = get_crew_manager()
        result = await manager.execute_crew(
            crew_type=crew_type,
            child_name=child.name,
            logs_text=logs_text,
            query=None,
        )
        
        if result.get("success"):
            monitor.log_crew_execution(
                crew_type=crew_type,
                child_name=child.name,
                tasks_executed=result.get("tasks_executed", 0),
            )
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Crew hatası: {str(e)}", exc_info=True)
        monitor.log_error("Crew", e, {"crew_type": crew_type, "child_id": child_id})
        
        return {
            "success": False,
            "error": str(e),
        }


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@router.get("/health")
def health_check():
    """Sistem Sağlığı Kontrolü"""
    monitor = get_monitor()
    stats = monitor.get_statistics()
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "workflow": "online",
            "crew": "online",
            "monitoring": "online",
        },
        "monitoring_stats": stats,
    }


@router.post("/reset-monitoring")
def reset_monitoring():
    """İzleme Verilerini Sıfırla"""
    monitor = get_monitor()
    perf_tracker = get_performance_tracker()
    
    monitor.clear_events()
    perf_tracker.reset()
    
    return {"status": "reset", "message": "İzleme verileri temizlendi"}
