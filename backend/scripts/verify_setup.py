#!/usr/bin/env python3
"""
Ortam değişkenleri, veritabanı ve CrewAI YAML yüklemesini doğrular.
Çalıştır: backend dizininden  ./venv/bin/python scripts/verify_setup.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
os.chdir(BACKEND)
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env")
os.environ.setdefault("CREWAI_STORAGE_DIR", "AutiCare")


def main() -> int:
    missing = [k for k in ("DATABASE_URL", "OPENAI_API_KEY") if not os.getenv(k)]
    if missing:
        print("Eksik ortam değişkenleri:", ", ".join(missing))
        print("  backend/.env dosyasını doldurun veya .env.example dosyasına bakın.")
    else:
        print("DATABASE_URL ve OPENAI_API_KEY tanımlı.")

    try:
        from sqlalchemy import create_engine, text

        url = os.getenv("DATABASE_URL")
        if not url:
            print("Veritabanı testi atlandı (DATABASE_URL yok).")
        else:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Veritabanı: bağlantı ve SELECT 1 başarılı.")
    except Exception as e:
        print("Veritabanı bağlanamadı:", e)
        print("  → MySQL çalışıyor mu? Docker Compose kullanıyorsanız: docker compose up -d")
        print("  → Yerel geliştirmede DATABASE_URL içinde host genelde 127.0.0.1 olur.")

    try:
        from app.services.crew_report import build_agents

        build_agents()
        print("CrewAI: agents.yaml ile ajanlar yüklendi.")
    except Exception as e:
        print("CrewAI / YAML hatası:", e)
        return 1

    print("\nSonraki adım (backend klasöründe):")
    print("  ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
