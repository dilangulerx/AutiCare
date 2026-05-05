"""
AutiCare MCP bridge and optional MCP stdio server.

This module has two responsibilities:
1) Provide safe, authorization-aware "tool" methods over existing DB models.
2) Optionally expose the same methods as a real MCP server (FastMCP) for agent runtimes.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from statistics import mean
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.daily_log import DailyLog
from app.models.reminder import Reminder
from app.models.weekly_report import WeeklyReport


class MCPAuthorizationError(Exception):
    """Raised when a user tries to access another parent's child data."""


class MCPValidationError(Exception):
    """Raised when tool input is missing/invalid."""


class AutiCareMCPBridge:
    """
    Safe bridge that maps MCP-like tool calls to AutiCare data/services.

    IMPORTANT:
    Every tool method enforces child ownership through `parent_id`.
    """

    def __init__(self, db: Session):
        self.db = db

    def _ensure_child_access(self, parent_id: int, child_id: int) -> Child:
        child = (
            self.db.query(Child)
            .filter(Child.id == child_id, Child.parent_id == parent_id)
            .first()
        )
        if not child:
            raise MCPAuthorizationError("Bu çocuğa erişim izniniz yok veya çocuk bulunamadı.")
        return child

    def get_child_logs(self, parent_id: int, child_id: int, days: int = 7) -> Dict[str, Any]:
        if days <= 0 or days > 90:
            raise MCPValidationError("days parametresi 1 ile 90 arasında olmalıdır.")

        child = self._ensure_child_access(parent_id, child_id)
        since = datetime.utcnow().date() - timedelta(days=days)

        logs = (
            self.db.query(DailyLog)
            .filter(DailyLog.child_id == child_id, DailyLog.date >= since)
            .order_by(DailyLog.date.desc())
            .all()
        )

        return {
            "child": {"id": child.id, "name": child.name},
            "days": days,
            "logs": [
                {
                    "id": log.id,
                    "date": str(log.date),
                    "eye_contact": log.eye_contact,
                    "communication_score": log.communication_score,
                    "aggression_level": log.aggression_level,
                    "sleep_hours": log.sleep_hours,
                    "notes": log.notes,
                }
                for log in logs
            ],
        }

    def query_child_metrics(
        self, parent_id: int, child_id: int, metric: str, days: int = 30
    ) -> Dict[str, Any]:
        metric_map = {
            "eye_contact": DailyLog.eye_contact,
            "communication_score": DailyLog.communication_score,
            "aggression_level": DailyLog.aggression_level,
            "sleep_hours": DailyLog.sleep_hours,
        }

        if metric not in metric_map:
            raise MCPValidationError(
                "metric şu değerlerden biri olmalı: eye_contact, communication_score, aggression_level, sleep_hours"
            )
        if days <= 1 or days > 180:
            raise MCPValidationError("days parametresi 2 ile 180 arasında olmalıdır.")

        child = self._ensure_child_access(parent_id, child_id)
        since = datetime.utcnow().date() - timedelta(days=days)
        metric_col = metric_map[metric]

        rows = (
            self.db.query(DailyLog.date, metric_col)
            .filter(DailyLog.child_id == child_id, DailyLog.date >= since)
            .order_by(DailyLog.date.asc())
            .all()
        )

        values = [float(value) for _, value in rows if value is not None]
        trend = "stable"
        if len(values) >= 4:
            first_half = values[: len(values) // 2]
            second_half = values[len(values) // 2 :]
            delta = mean(second_half) - mean(first_half)
            if delta > 0.3:
                trend = "increasing"
            elif delta < -0.3:
                trend = "decreasing"

        return {
            "child": {"id": child.id, "name": child.name},
            "metric": metric,
            "days": days,
            "samples": [{"date": str(day), "value": value} for day, value in rows],
            "summary": {
                "count": len(values),
                "average": round(mean(values), 2) if values else None,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "trend": trend,
            },
        }

    def get_weekly_summary(self, parent_id: int, child_id: int) -> Dict[str, Any]:
        child = self._ensure_child_access(parent_id, child_id)
        since = datetime.utcnow().date() - timedelta(days=7)

        logs = (
            self.db.query(DailyLog)
            .filter(DailyLog.child_id == child_id, DailyLog.date >= since)
            .order_by(DailyLog.date.asc())
            .all()
        )

        def avg_of(attr_name: str) -> float | None:
            nums = [float(getattr(log, attr_name)) for log in logs if getattr(log, attr_name) is not None]
            return round(mean(nums), 2) if nums else None

        latest_report = (
            self.db.query(WeeklyReport)
            .filter(WeeklyReport.child_id == child_id)
            .order_by(WeeklyReport.generated_at.desc())
            .first()
        )

        return {
            "child": {"id": child.id, "name": child.name},
            "period": "last_7_days",
            "log_count": len(logs),
            "averages": {
                "eye_contact": avg_of("eye_contact"),
                "communication_score": avg_of("communication_score"),
                "aggression_level": avg_of("aggression_level"),
                "sleep_hours": avg_of("sleep_hours"),
            },
            "latest_report": {
                "id": latest_report.id,
                "week_start_date": str(latest_report.week_start_date),
                "generated_at": latest_report.generated_at.isoformat() if latest_report.generated_at else None,
            }
            if latest_report
            else None,
        }

    def add_reminder(
        self,
        parent_id: int,
        child_id: int,
        title: str,
        remind_at_iso: str,
        description: str | None = None,
    ) -> Dict[str, Any]:
        if not title.strip():
            raise MCPValidationError("title boş olamaz.")

        try:
            remind_at = datetime.fromisoformat(remind_at_iso)
        except ValueError as exc:
            raise MCPValidationError("remind_at_iso geçerli bir ISO datetime olmalıdır.") from exc

        self._ensure_child_access(parent_id, child_id)
        reminder = Reminder(
            child_id=child_id,
            title=title.strip(),
            description=description,
            remind_at=remind_at,
        )
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)

        return {
            "id": reminder.id,
            "child_id": reminder.child_id,
            "title": reminder.title,
            "remind_at": reminder.remind_at.isoformat(),
            "is_active": reminder.is_active,
        }

    def generate_therapy_brief(self, parent_id: int, child_id: int, days: int = 14) -> Dict[str, Any]:
        child = self._ensure_child_access(parent_id, child_id)
        logs_payload = self.get_child_logs(parent_id=parent_id, child_id=child_id, days=days)["logs"]
        summary = self.get_weekly_summary(parent_id=parent_id, child_id=child_id)

        if not logs_payload:
            brief = (
                f"{child.name} icin son {days} gunde kayit bulunamadi. "
                "Doktor gorusmesi oncesi guncel gozlem verilerinin sisteme eklenmesi onerilir."
            )
        else:
            avg = summary["averages"]
            brief = (
                f"{child.name} icin son {days} gunun ozetinde "
                f"goz temasi ortalamasi {avg['eye_contact']}, "
                f"iletisim puani ortalamasi {avg['communication_score']}, "
                f"agresyon seviyesi ortalamasi {avg['aggression_level']} ve "
                f"uyku suresi ortalamasi {avg['sleep_hours']} saattir. "
                "Bu metin bilgilendirme amaclidir; klinik tani yerine gecmez."
            )

        return {
            "child": {"id": child.id, "name": child.name},
            "days": days,
            "brief_text": brief,
            "safety_note": "Bu cikti medikal tani degildir; uzman degerlendirmesi gerekir.",
        }


def _register_fastmcp_tools(mcp: Any) -> None:
    """
    Register tool signatures for stdio MCP runtimes.
    This function is isolated so core app never depends on mcp package at import time.
    """

    @mcp.tool()
    def get_child_logs(parent_id: int, child_id: int, days: int = 7) -> Dict[str, Any]:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            bridge = AutiCareMCPBridge(db)
            return bridge.get_child_logs(parent_id=parent_id, child_id=child_id, days=days)
        finally:
            db.close()

    @mcp.tool()
    def query_child_metrics(parent_id: int, child_id: int, metric: str, days: int = 30) -> Dict[str, Any]:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            bridge = AutiCareMCPBridge(db)
            return bridge.query_child_metrics(
                parent_id=parent_id,
                child_id=child_id,
                metric=metric,
                days=days,
            )
        finally:
            db.close()

    @mcp.tool()
    def add_reminder(
        parent_id: int,
        child_id: int,
        title: str,
        remind_at_iso: str,
        description: str | None = None,
    ) -> Dict[str, Any]:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            bridge = AutiCareMCPBridge(db)
            return bridge.add_reminder(
                parent_id=parent_id,
                child_id=child_id,
                title=title,
                remind_at_iso=remind_at_iso,
                description=description,
            )
        finally:
            db.close()

    @mcp.tool()
    def get_weekly_summary(parent_id: int, child_id: int) -> Dict[str, Any]:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            bridge = AutiCareMCPBridge(db)
            return bridge.get_weekly_summary(parent_id=parent_id, child_id=child_id)
        finally:
            db.close()

    @mcp.tool()
    def generate_therapy_brief(parent_id: int, child_id: int, days: int = 14) -> Dict[str, Any]:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            bridge = AutiCareMCPBridge(db)
            return bridge.generate_therapy_brief(parent_id=parent_id, child_id=child_id, days=days)
        finally:
            db.close()


def build_fastmcp_server() -> Any:
    """
    Build and return FastMCP server instance if package is available.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - runtime dependency guard
        raise RuntimeError(
            "mcp paketi bulunamadi. `pip install -r requirements.txt` ile bagimliliklari yukleyin."
        ) from exc

    mcp = FastMCP("auticare-mcp-server")
    _register_fastmcp_tools(mcp)
    return mcp


def run_stdio_server() -> None:
    """
    Entry-point for running MCP over stdio transport.
    """
    mcp = build_fastmcp_server()
    mcp.run()
