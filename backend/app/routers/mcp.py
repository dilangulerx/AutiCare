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

#kim olduguna bakılıyor gercek user mi 
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

    try:
        result = _resolve_advisor_reply(bridge, current_user, request)
        return result
    except (MCPValidationError, MCPAuthorizationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _interpret_score(value, metric_type="positive"):
    """Metrik değerini sözel yoruma çevir (1-5 ölçek)."""
    if value is None:
        return "veri yok"
    if metric_type == "positive":  # göz teması, iletişim (yüksek = iyi)
        if value >= 4:
            return "çok iyi"
        if value >= 3:
            return "iyi"
        if value >= 2:
            return "orta"
        return "düşük"
    else:  # agresyon (düşük = iyi)
        if value <= 1.5:
            return "çok düşük (olumlu)"
        if value <= 2.5:
            return "düşük (olumlu)"
        if value <= 3.5:
            return "orta"
        return "yüksek (dikkat gerektirir)"


def _build_progress_reply(child_name, log_count, eye_val, comm_val, agg_val, sleep_val):
    """
    Verilere dayalı, sıcak ve doğal dilde gelişim özeti üret.
    Her metriği gözlem + yorum + pratik öneri olarak tek akışta yazar.
    """

    parts = [f"Merhaba! {child_name} için son 7 güne ait {log_count} kayda baktım. İşte gördüklerim:\n"]

    # ── Göz Teması ──
    if eye_val is not None:
        if eye_val >= 4:
            parts.append(
                f"👁️ Göz teması ortalaması {eye_val}/5 — harika bir seviye! "
                f"{child_name} iletişim sırasında göz teması kurmaya devam ediyor. "
                "Bu ilerlemeyi pekiştirmek için birlikte oynama anlarında onu takdir etmeye devam edin."
            )
        elif eye_val >= 3:
            parts.append(
                f"👁️ Göz teması ortalaması {eye_val}/5 — iyi bir seviye. "
                "Yemek ve oyun gibi doğal anlarda göz teması fırsatları yaratmaya devam ederseniz "
                "bu alanda daha da ilerleme görebilirsiniz."
            )
        elif eye_val >= 2:
            parts.append(
                f"👁️ Göz teması ortalaması {eye_val}/5 — biraz düşük, ama geliştirebileceğiniz bir alan. "
                f"Pratik öneri: {child_name} ile konuşurken göz hizasına inin ve ilgisini çeken "
                "nesneleri yüzünüz seviyesinde tutun. Zorlama yerine doğal anlarda spontan göz temasını "
                "küçük bir gülümsemeyle ödüllendirmeyi deneyin."
            )
        else:
            parts.append(
                f"👁️ Göz teması ortalaması {eye_val}/5 — bu alan dikkat istiyor. "
                f"Pratik öneri: {child_name}'in sevdiği oyuncakları veya atıştırmalıkları "
                "göz hizasında tutarak kısa anlık göz teması fırsatları yaratabilirsiniz. "
                "'Bana bak' gibi yönergeler yerine, ilgisini çeken bir aktivite sırasında "
                "doğal temas anlarını yakalamak daha etkili olacaktır."
            )

    # ── İletişim ──
    if comm_val is not None:
        if comm_val >= 4:
            parts.append(
                f"\n💬 İletişim skoru {comm_val}/5 — güçlü bir seviye! "
                f"{child_name} kendini ifade etmede iyi bir noktada. "
                "Karşılıklı sohbet fırsatlarını artırarak bu gelişimi desteklemeye devam edebilirsiniz."
            )
        elif comm_val >= 3:
            parts.append(
                f"\n💬 İletişim skoru {comm_val}/5 — güzel bir ilerleme var. "
                "Günlük rutinlerde kısa diyaloglar kurmaya devam edin. "
                f"Örneğin {child_name}'in söylediklerini genişleterek tekrarlamak "
                "('Su istiyorum' → 'Soğuk su istiyorsun, tamam!') dil gelişimini destekler."
            )
        elif comm_val >= 2:
            parts.append(
                f"\n💬 İletişim skoru {comm_val}/5 — gelişim sürecinde. "
                f"Pratik öneri: {child_name}'e basit seçenekler sunun (örn: 'Elma mı, muz mu?'). "
                "Her iletişim girişimini — ister jest, ister ses, ister sözcük olsun — "
                "hemen karşılık vererek ödüllendirin. Birlikte kitap bakma ve şarkı söyleme de çok faydalıdır."
            )
        else:
            parts.append(
                f"\n💬 İletişim skoru {comm_val}/5 — bu alanda desteğe ihtiyaç var. "
                "Pratik öneri: Görsel destek kartları (PECS) kullanmayı deneyebilirsiniz. "
                f"{child_name}'in her türlü iletişim girişimini (jest, mimik, ses) "
                "hemen karşılık vererek teşvik edin. Uzman dil-konuşma terapisi de bu aşamada değerli olabilir."
            )

    # ── Agresyon ──
    if agg_val is not None:
        if agg_val <= 1.5:
            parts.append(
                f"\n😊 Agresyon seviyesi {agg_val}/5 — çok olumlu! "
                f"{child_name} sakin ve dengeli bir hafta geçirmiş. "
                "Mevcut rutinleri korumaya devam etmeniz bu güzel tabloyu sürdürecektir."
            )
        elif agg_val <= 2.5:
            parts.append(
                f"\n😊 Agresyon seviyesi {agg_val}/5 — normal sınırlar içinde. "
                "Olumlu davranışları tutarlı şekilde takdir etmeye devam etmeniz "
                "bu dengeyi koruyacaktır."
            )
        elif agg_val <= 3.5:
            parts.append(
                f"\n😤 Agresyon seviyesi {agg_val}/5 — orta düzeyde, biraz yükselmiş. "
                "Pratik öneri: Düzenli mola zamanları planlayın ve geçişlerden önce "
                f"5 dakika öncesinden {child_name}'i uyarın. "
                "Duygularını ifade etmesi için alternatif yollar öğretmek (derin nefes, yastığa vurmak) "
                "bu dönemde çok işe yarayabilir."
            )
        else:
            parts.append(
                f"\n⚠️ Agresyon seviyesi {agg_val}/5 — yüksek, dikkat gerektiriyor. "
                "Pratik öneri: Tetikleyicileri not edin (açlık, yorgunluk, aşırı uyaran, geçişler). "
                "Bir 'sakinleşme köşesi' oluşturun ve kriz anında sakin, kısa cümleler kullanın. "
                "Bu seviye devam ederse uzman desteği almanızı öneririm."
            )

    # ── Uyku ──
    if sleep_val is not None:
        if sleep_val < 7:
            parts.append(
                f"\n😴 Uyku ortalaması {sleep_val} saat — yetersiz kalıyor. "
                "Düşük uyku gün içinde sinirlilik ve odaklanma güçlüğüne yol açabilir. "
                "Pratik öneri: Sabit bir yatış saati belirleyin, yatmadan 1 saat önce ekranları kapatın "
                "ve sakinleştirici bir gece rutini oluşturun (ılık banyo, ninni veya hafif müzik). "
                "Kronik uyku sorunu varsa pediatristinize danışmanızı öneririm."
            )
        elif sleep_val > 11:
            parts.append(
                f"\n😴 Uyku ortalaması {sleep_val} saat — normalden yüksek. "
                "Aşırı uyku altta yatan yorgunluk veya sağlık durumlarına işaret edebilir. "
                "Gündüz aktivite düzeyini artırmayı deneyin; devam ederse doktorunuzla paylaşın."
            )
        else:
            parts.append(
                f"\n😴 Uyku ortalaması {sleep_val} saat — sağlıklı bir düzen! "
                "Düzenli uyku-uyanma saatlerini korumaya devam edin."
            )

    # ── Kapanış ──
    parts.append(
        "\n⚕️ Bu değerlendirme kayıtlarınıza dayanmaktadır ve tıbbi teşhis yerine geçmez. "
        "Herhangi bir konuda daha detaylı bilgi isterseniz sormaktan çekinmeyin!"
    )

    return "\n".join(parts)



def _resolve_advisor_reply(
    bridge: AutiCareMCPBridge,
    current_user: Any,
    request: AdvisorRequest,
) -> Dict[str, Any]:
    msg = request.message.lower()

    # ── 1. Hatırlatıcı oluşturma ──
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

    # ── 2. Terapi özeti / rapor ──
    if "özet" in msg or "ozet" in msg or "terapi" in msg:
        brief = bridge.generate_therapy_brief(
            parent_id=current_user.id,
            child_id=request.child_id,
        )
        return {"reply": brief["brief_text"], "action": "therapy_brief", "tool_result": brief}

    # ── 3. Spesifik metrik sorguları ──
    # Uyku
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

    # Göz teması
    if any(kw in msg for kw in ("göz", "goz", "göz teması", "goz temasi", "bakış", "bakis")):
        metric_data = bridge.query_child_metrics(
            parent_id=current_user.id,
            child_id=request.child_id,
            metric="eye_contact",
            days=30,
        )
        summary = metric_data["summary"]
        child_name = metric_data["child"]["name"]
        trend_tr = {"increasing": "artış eğiliminde", "decreasing": "düşüş eğiliminde", "stable": "stabil"}.get(summary["trend"], summary["trend"])
        return {
            "reply": (
                f"{child_name} için son 30 günde göz teması ortalaması 5 üzerinden {summary['average']}. "
                f"En düşük: {summary['min']}, en yüksek: {summary['max']}. Genel trend: {trend_tr}. "
                "Bu bilgi klinik değerlendirme yerine geçmez."
            ),
            "action": "eye_contact_metric",
            "tool_result": metric_data,
        }

    # İletişim
    if any(kw in msg for kw in ("iletişim", "iletisim", "konuşma", "konusma", "kelime", "söz", "soz")):
        metric_data = bridge.query_child_metrics(
            parent_id=current_user.id,
            child_id=request.child_id,
            metric="communication_score",
            days=30,
        )
        summary = metric_data["summary"]
        child_name = metric_data["child"]["name"]
        trend_tr = {"increasing": "artış eğiliminde", "decreasing": "düşüş eğiliminde", "stable": "stabil"}.get(summary["trend"], summary["trend"])
        return {
            "reply": (
                f"{child_name} için son 30 günde iletişim skoru ortalaması 5 üzerinden {summary['average']}. "
                f"En düşük: {summary['min']}, en yüksek: {summary['max']}. Genel trend: {trend_tr}. "
                "İletişimde olumlu değişimleri desteklemek için günlük etkileşim rutinleri faydalı olabilir."
            ),
            "action": "communication_metric",
            "tool_result": metric_data,
        }

    # Agresyon / saldırganlık
    if any(kw in msg for kw in ("agresyon", "saldırgan", "saldirgan", "öfke", "ofke", "sinir", "kriz", "tantrum")):
        metric_data = bridge.query_child_metrics(
            parent_id=current_user.id,
            child_id=request.child_id,
            metric="aggression_level",
            days=30,
        )
        summary = metric_data["summary"]
        child_name = metric_data["child"]["name"]
        trend_tr = {"increasing": "artış eğiliminde", "decreasing": "düşüş eğiliminde", "stable": "stabil"}.get(summary["trend"], summary["trend"])
        return {
            "reply": (
                f"{child_name} için son 30 günde agresyon seviyesi ortalaması 5 üzerinden {summary['average']}. "
                f"En düşük: {summary['min']}, en yüksek: {summary['max']}. Genel trend: {trend_tr}. "
                "Agresyon artışı gözlemliyorsanız tetikleyici faktörleri not etmeniz faydalı olabilir."
            ),
            "action": "aggression_metric",
            "tool_result": metric_data,
        }

    # ── 4. Genel gelişim / durum / hafta soruları ──
    # "Ali'nin bu haftaki gelişimi nasıl?" gibi sorular buraya düşer
    _progress_keywords = (
        "gelişim", "gelisim", "nasıl", "nasil", "durum", "gidiş", "gidis",
        "hafta", "ilerleme", "değişim", "degisim", "performans", "puan",
        "skor", "rapor", "genel", "son", "bugün", "bugun", "dün", "dun",
        "davranış", "davranis", "ne durumda",
    )
    if any(kw in msg for kw in _progress_keywords):
        weekly = bridge.get_weekly_summary(parent_id=current_user.id, child_id=request.child_id)
        child_name = weekly["child"]["name"]
        avg = weekly["averages"]
        log_count = weekly["log_count"]

        if log_count == 0:
            return {
                "reply": (
                    f"{child_name} için son 7 günde henüz kayıt bulunmuyor. "
                    "Günlük kayıt ekleyerek gelişimi takip etmeye başlayabilirsiniz."
                ),
                "action": "progress_no_data",
                "tool_result": weekly,
            }

        # Verileri al
        eye_val = avg.get("eye_contact")
        comm_val = avg.get("communication_score")
        agg_val = avg.get("aggression_level")
        sleep_val = avg.get("sleep_hours")

        reply_text = _build_progress_reply(child_name, log_count, eye_val, comm_val, agg_val, sleep_val)
        return {
            "reply": reply_text,
            "action": "progress_summary",
            "tool_result": weekly,
        }

    # ── 5. Fallback — tanınmayan sorular için de veri-bazlı yanıt ──
    weekly = bridge.get_weekly_summary(parent_id=current_user.id, child_id=request.child_id)
    child_name = weekly["child"]["name"]
    avg = weekly["averages"]
    log_count = weekly["log_count"]

    if log_count == 0:
        fallback_reply = (
            f"{child_name} için henüz yeterli veri bulunmuyor. "
            "Günlük kayıt ekledikçe size daha detaylı bilgi verebilirim.\n\n"
            "💡 Şu konularda yardımcı olabilirim:\n"
            "• 'Bu haftaki gelişimi nasıl?'\n"
            "• 'Göz teması trendi'\n"
            "• 'Uyku durumu'\n"
            "• 'İletişim nasıl?'\n"
            "• 'Terapi özeti'\n"
            "• 'Hatırlatıcı oluştur'"
        )
    else:
        eye_val = avg.get("eye_contact")
        comm_val = avg.get("communication_score")
        agg_val = avg.get("aggression_level")
        sleep_val = avg.get("sleep_hours")
        fallback_reply = _build_progress_reply(child_name, log_count, eye_val, comm_val, agg_val, sleep_val)

    return {
        "reply": fallback_reply,
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
