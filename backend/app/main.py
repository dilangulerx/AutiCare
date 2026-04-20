import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Configuration ve validation yükle (startup'ta kritik ayarları kontrol et)
from app.config import settings

# CrewAI 1.x: appdirs ile yerel veri yolu; yoksa cwd adı kullanılır (ör. "backend")
os.environ.setdefault("CREWAI_STORAGE_DIR", settings.CREWAI_STORAGE_DIR)

from app.database import create_tables
from app.routers import auth, children, daily_logs, weekly_reports, reminders
from app.services.scheduler import start_scheduler, stop_scheduler
from app.routers import ai
from app.monitoring import get_monitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Otizm Gelişim Takip API",
    description="Otizmli çocukların gelişimini takip eden Agentic AI destekli API (LangGraph + CrewAI Hibrit Sistem - Search, HITL, Dinamik Rota)",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

app.include_router(auth.router)
app.include_router(children.router)
app.include_router(daily_logs.router)
app.include_router(weekly_reports.router)
app.include_router(reminders.router)
app.include_router(ai.router)

@app.on_event("startup")
def startup():
    """Uygulama Başlangıcı"""
    logger.info("🚀 AutiCare API Başlatılıyor...")
    
    # Scheduler'ı başlat
    start_scheduler()
    
    # Monitoring başlat
    monitor = get_monitor()
    logger.info(f"✓ Monitoring sistemi aktif (LangSmith: {monitor.tracking_enabled})")
    
    # Workflow'u başlat
    try:
        from app.workflow import get_workflow_executor
        executor = get_workflow_executor()
        info = executor.get_workflow_info()
        logger.info(f"✓ LangGraph Workflow: {info['name']}")
    except Exception as e:
        logger.warning(f"⚠️ Workflow yükleme uyarısı: {e}")
    
    # CrewAI'ı başlat
    try:
        from app.crew_manager import get_crew_manager
        manager = get_crew_manager()
        info = manager.get_crew_info()
        logger.info(f"✓ CrewAI: {info['agents_loaded']} ajan, {info['tasks_loaded']} görev yüklü")
    except Exception as e:
        logger.warning(f"⚠️ CrewAI yükleme uyarısı: {e}")
    
    logger.info("🎯 AutiCare API Hazır!")

@app.on_event("shutdown")
def shutdown():
    """Uygulama Kapanışı"""
    logger.info("🛑 AutiCare API Kapanıyor...")
    stop_scheduler()
    logger.info("✓ Kapatıldı")

@app.get("/")
def root():
    return {
        "message": "Otizm Takip API çalışıyor 🚀",
        "version": "2.0.0",
        "system": "LangGraph + CrewAI Hibrit AI"
    }

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
