import asyncio
import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.database import get_db
from app.routers.auth import get_current_user
from app.services.auth import decode_token, get_user_by_id
from app.services.mcp_server import (
    AutiCareMCPBridge,
    MCPAuthorizationError,
    MCPValidationError,
)

router = APIRouter(prefix="/mcp", tags=["MCP"])


class MCPToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class AdvisorRequest(BaseModel):
    message: str
    child_id: int
    schedule_time_iso: Optional[str] = None


@router.get("/tools")
def list_tools(current_user=Depends(get_current_user)):
    # current_user dependency enforces authentication.
    return {
        "tools": [
            {
                "name": "get_child_logs",
                "description": "Belirli bir cocugun son X gunluk loglarini getirir.",
                "required_arguments": ["child_id"],
                "optional_arguments": ["days"],
            },
            {
                "name": "query_child_metrics",
                "description": "Belirli bir metrik icin tarihsel trend ozetini verir.",
                "required_arguments": ["child_id", "metric"],
                "optional_arguments": ["days"],
            },
            {
                "name": "get_weekly_summary",
                "description": "Son 7 gunun ozet ortalamalarini verir.",
                "required_arguments": ["child_id"],
                "optional_arguments": [],
            },
            {
                "name": "add_reminder",
                "description": "Cocuga yeni bir hatirlatici ekler.",
                "required_arguments": ["child_id", "title", "remind_at_iso"],
                "optional_arguments": ["description"],
            },
            {
                "name": "generate_therapy_brief",
                "description": "Doktor gorusmesi oncesi kisa terapi ozeti uretir.",
                "required_arguments": ["child_id"],
                "optional_arguments": ["days"],
            },
        ]
    }


@router.post("/call")
def call_tool(
    request: MCPToolCallRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bridge = AutiCareMCPBridge(db)
    args = request.arguments

    try:
        if request.tool_name == "get_child_logs":
            return bridge.get_child_logs(
                parent_id=current_user.id,
                child_id=int(args["child_id"]),
                days=int(args.get("days", 7)),
            )
        if request.tool_name == "query_child_metrics":
            return bridge.query_child_metrics(
                parent_id=current_user.id,
                child_id=int(args["child_id"]),
                metric=str(args["metric"]),
                days=int(args.get("days", 30)),
            )
        if request.tool_name == "get_weekly_summary":
            return bridge.get_weekly_summary(
                parent_id=current_user.id,
                child_id=int(args["child_id"]),
            )
        if request.tool_name == "add_reminder":
            return bridge.add_reminder(
                parent_id=current_user.id,
                child_id=int(args["child_id"]),
                title=str(args["title"]),
                remind_at_iso=str(args["remind_at_iso"]),
                description=args.get("description"),
            )
        if request.tool_name == "generate_therapy_brief":
            return bridge.generate_therapy_brief(
                parent_id=current_user.id,
                child_id=int(args["child_id"]),
                days=int(args.get("days", 14)),
            )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Eksik arguman: {exc.args[0]}") from exc
    except MCPValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MCPAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    raise HTTPException(status_code=404, detail="Bilinmeyen MCP araci")


@router.post("/advisor")
def conversational_advisor(
    request: AdvisorRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lightweight conversational advisor route using MCP tools internally.
    This provides a production-safe stepping stone before full LLM tool-calling.
    """
    bridge = AutiCareMCPBridge(db)
    msg = request.message.lower()

    try:
        if "hatırlat" in msg or "hatirlat" in msg:
            if not request.schedule_time_iso:
                return {
                    "reply": "Hatirlatici olusturabilmem icin lutfen schedule_time_iso gonderin (ISO format).",
                    "action": "missing_schedule_time",
                }
            reminder = bridge.add_reminder(
                parent_id=current_user.id,
                child_id=request.child_id,
                title="AI Onerisi: Destekleyici rutin",
                remind_at_iso=request.schedule_time_iso,
                description="Konusma asistaninin onerisiyle olusturuldu.",
            )
            return {
                "reply": "Hatirlaticiyi olusturdum. Rutin uygulanabilirligi icin gunluk geri bildirim ekleyebilirsiniz.",
                "action": "reminder_created",
                "tool_result": reminder,
            }

        if "özet" in msg or "ozet" in msg or "terapi" in msg:
            brief = bridge.generate_therapy_brief(
                parent_id=current_user.id,
                child_id=request.child_id,
            )
            return {"reply": brief["brief_text"], "action": "therapy_brief", "tool_result": brief}

        if "uyku" in msg:
            metric_data = bridge.query_child_metrics(
                parent_id=current_user.id,
                child_id=request.child_id,
                metric="sleep_hours",
                days=30,
            )
            summary = metric_data["summary"]
            return {
                "reply": (
                    f"Son 30 gunde uyku ortalamasi {summary['average']} saat, trend: {summary['trend']}. "
                    "Bu bilgi tani yerine gecmez; klinik degerlendirme icin uzmana basvurun."
                ),
                "action": "sleep_metric_summary",
                "tool_result": metric_data,
            }

        weekly = bridge.get_weekly_summary(parent_id=current_user.id, child_id=request.child_id)
        return {
            "reply": (
                "Son 7 gun ozetini cektim. Sorunuzu daha netlestirirseniz "
                "ilgili metrikte daha spesifik analiz yapabilirim."
            ),
            "action": "weekly_summary",
            "tool_result": weekly,
        }
    except (MCPValidationError, MCPAuthorizationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _resolve_advisor_reply(
    bridge: AutiCareMCPBridge,
    current_user: Any,
    request: AdvisorRequest,
) -> Dict[str, Any]:
    msg = request.message.lower()
    if "hatırlat" in msg or "hatirlat" in msg:
        if not request.schedule_time_iso:
            return {
                "reply": "Hatirlatici olusturabilmem icin lutfen schedule_time_iso gonderin (ISO format).",
                "action": "missing_schedule_time",
            }
        reminder = bridge.add_reminder(
            parent_id=current_user.id,
            child_id=request.child_id,
            title="AI Onerisi: Destekleyici rutin",
            remind_at_iso=request.schedule_time_iso,
            description="Konusma asistaninin onerisiyle olusturuldu.",
        )
        return {
            "reply": "Hatirlaticiyi olusturdum. Rutin uygulanabilirligi icin gunluk geri bildirim ekleyebilirsiniz.",
            "action": "reminder_created",
            "tool_result": reminder,
        }

    if "özet" in msg or "ozet" in msg or "terapi" in msg:
        brief = bridge.generate_therapy_brief(
            parent_id=current_user.id,
            child_id=request.child_id,
        )
        return {"reply": brief["brief_text"], "action": "therapy_brief", "tool_result": brief}

    if "uyku" in msg:
        metric_data = bridge.query_child_metrics(
            parent_id=current_user.id,
            child_id=request.child_id,
            metric="sleep_hours",
            days=30,
        )
        summary = metric_data["summary"]
        return {
            "reply": (
                f"Son 30 gunde uyku ortalamasi {summary['average']} saat, trend: {summary['trend']}. "
                "Bu bilgi tani yerine gecmez; klinik degerlendirme icin uzmana basvurun."
            ),
            "action": "sleep_metric_summary",
            "tool_result": metric_data,
        }

    weekly = bridge.get_weekly_summary(parent_id=current_user.id, child_id=request.child_id)
    return {
        "reply": (
            "Son 7 gun ozetini cektim. Sorunuzu daha netlestirirseniz "
            "ilgili metrikte daha spesifik analiz yapabilirim."
        ),
        "action": "weekly_summary",
        "tool_result": weekly,
    }


@router.get("/advisor/stream")
async def conversational_advisor_stream(
    token: str,
    child_id: int,
    message: str,
    schedule_time_iso: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Gecersiz token")
    current_user = get_user_by_id(db, user_id)
    if not current_user:
        raise HTTPException(status_code=401, detail="Kullanici bulunamadi")

    bridge = AutiCareMCPBridge(db)
    request = AdvisorRequest(
        message=message,
        child_id=child_id,
        schedule_time_iso=schedule_time_iso,
    )
    try:
        advisor_payload = _resolve_advisor_reply(bridge, current_user, request)
        reply_text = advisor_payload["reply"]
    except (MCPValidationError, MCPAuthorizationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def event_generator():
        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        words = reply_text.split(" ")
        chunk = []
        for idx, word in enumerate(words):
            chunk.append(word)
            if len(chunk) >= 4 or idx == len(words) - 1:
                text = " ".join(chunk) + " "
                yield f"data: {json.dumps({'type': 'chunk', 'text': text})}\n\n"
                chunk = []
                await asyncio.sleep(0.05)
        yield f"data: {json.dumps({'type': 'done', 'tool_result': advisor_payload.get('tool_result')})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
