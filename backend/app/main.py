from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.database import create_tables
from app.routers import auth, children, daily_logs, weekly_reports, reminders
from app.services.scheduler import start_scheduler, stop_scheduler
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Otizm Gelişim Takip API",
    description="Otizmli çocukların gelişimini takip eden AI destekli API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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

@app.on_event("startup")
def startup():
    start_scheduler()

@app.on_event("shutdown")
def shutdown():
    stop_scheduler()

@app.get("/")
def root():
    return {"message": "Otizm Takip API çalışıyor 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}