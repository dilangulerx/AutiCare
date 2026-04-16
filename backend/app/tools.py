"""
AutiCare Custom Tools
Ajanların kullanacağı özel araçlar: arama, veritabanı sorgulama, rapor oluşturma.

NEDEN BU MODÜL?
- Mevcut sistemde ajanlar sadece kendilerine verilen logs_data ile sınırlıydı.
- Artık internetten güncel terapi bilgisi arayabilir, veritabanını sorgulayabilir
  ve zengin raporlar üretebilirler.
"""

import json
import logging
from typing import Optional
from datetime import datetime, timedelta

from crewai.tools import BaseTool
from pydantic import Field

logger = logging.getLogger(__name__)


# =============================================================================
# 1) ARAMA ARACI — İnternetten güncel bilgi toplamak için
# =============================================================================

class AutismResearchSearchTool(BaseTool):
    """
    Otizm araştırma arama aracı.
    
    NEDEN?
    TherapyAdvisorAgent ve LiteratureReviewAgent'ın güncel akademik
    kaynaklara ve terapi kılavuzlarına erişebilmesi gerekiyor.
    Mevcut sistemde ajanlar sadece sağlanan verilere bağımlıydı;
    bu araç sayesinde proaktif olarak bilgi toplayabilirler.
    """
    name: str = "autism_research_search"
    description: str = (
        "Otizm spektrum bozukluğu, davranış terapileri, ABA terapisi, "
        "duyusal entegrasyon ve çocuk gelişimi ile ilgili güncel bilgileri "
        "internetten arar. Anahtar kelime(ler) girin."
    )

    def _run(self, query: str) -> str:
        try:
            from duckduckgo_search import DDGS

            safe_query = f"autism therapy {query}"
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(safe_query, max_results=5):
                    results.append({
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                        "href": r.get("href", ""),
                    })

            if not results:
                return "Arama sonucu bulunamadı."

            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(
                    f"{i}. {r['title']}\n   {r['body']}\n   Kaynak: {r['href']}"
                )
            return "\n\n".join(formatted)

        except ImportError:
            return "Arama aracı kullanılamıyor (duckduckgo-search yüklü değil)."
        except Exception as e:
            logger.error(f"Arama hatası: {e}")
            return f"Arama sırasında hata oluştu: {str(e)}"


# =============================================================================
# 2) VERİTABANI SORGULAMA ARACI — Geçmiş verilere erişim
# =============================================================================

class DatabaseQueryTool(BaseTool):
    """
    Çocuğun davranışsal veritabanını sorgulama aracı.

    NEDEN?
    DataAnalystAgent'ın son 30 günlük veriden daha fazlasına erişmesi,
    özel filtreler uygulaması gerekebilir. Bu araç, ajanların
    veritabanından belirli kriterlere göre veri çekmesini sağlar.
    SQL injection koruması için parametrize sorgular kullanılır.
    """
    name: str = "database_query"
    description: str = (
        "Çocuğun davranışsal veritabanını sorgular. "
        "JSON formatında filtre parametreleri girin: "
        '{"child_id": 1, "days": 30, "field": "sleep_hours", "min_value": 0}'
    )

    def _run(self, query_params: str) -> str:
        try:
            params = json.loads(query_params)
        except json.JSONDecodeError:
            return "Geçersiz JSON formatı. Örnek: {\"child_id\": 1, \"days\": 30}"

        try:
            from app.database import SessionLocal
            from app.models.daily_log import DailyLog

            db = SessionLocal()
            try:
                child_id = params.get("child_id")
                days = min(params.get("days", 30), 90)  # Maks 90 gün
                field = params.get("field")
                min_value = params.get("min_value")

                if not child_id:
                    return "child_id parametresi zorunludur."

                since = datetime.now() - timedelta(days=days)

                q = db.query(DailyLog).filter(
                    DailyLog.child_id == int(child_id),
                    DailyLog.date >= since.date(),
                )

                logs = q.order_by(DailyLog.date.desc()).all()

                results = []
                for log in logs:
                    entry = {
                        "date": str(log.date),
                        "eye_contact": log.eye_contact,
                        "communication_score": log.communication_score,
                        "aggression_level": log.aggression_level,
                        "sleep_hours": log.sleep_hours,
                        "notes": log.notes,
                    }
                    # İsteğe bağlı alan filtresi
                    if field and min_value is not None:
                        val = entry.get(field)
                        if val is not None and float(val) >= float(min_value):
                            results.append(entry)
                    else:
                        results.append(entry)

                return json.dumps(results, ensure_ascii=False, indent=2)
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Veritabanı sorgu hatası: {e}")
            return f"Veritabanı sorgulama hatası: {str(e)}"


# =============================================================================
# 3) RAPOR OLUŞTURMA ARACI — Zengin format raporlar
# =============================================================================

class ReportFormatterTool(BaseTool):
    """
    Davranışsal raporları yapılandırılmış formata dönüştürme aracı.

    NEDEN?
    ReportGeneratorAgent'ın ürettiği ham çıktıyı, ebeveynlere
    ve terapistlere sunulabilecek profesyonel bir formata
    dönüştürmek gerekiyor.
    """
    name: str = "report_formatter"
    description: str = (
        "Ham rapor metnini yapılandırılmış JSON formatına dönüştürür. "
        "Rapor metnini ve rapor türünü girin."
    )

    def _run(self, raw_report: str) -> str:
        try:
            now = datetime.now()
            structured = {
                "report_metadata": {
                    "generated_at": now.isoformat(),
                    "format_version": "2.0",
                    "report_type": "weekly_behavioral",
                },
                "sections": [],
            }

            # Ham raporu bölümlere ayır
            lines = raw_report.strip().split("\n")
            current_section = {"title": "Genel", "content": []}

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                # Başlık satırları (emoji veya # ile başlayan)
                if stripped.startswith(("#", "📊", "⚠️", "💡", "===", "---")):
                    if current_section["content"]:
                        structured["sections"].append(current_section)
                    current_section = {
                        "title": stripped.lstrip("#📊⚠️💡=- ").strip(),
                        "content": [],
                    }
                else:
                    current_section["content"].append(stripped)

            if current_section["content"]:
                structured["sections"].append(current_section)

            return json.dumps(structured, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Rapor biçimlendirme hatası: {e}")
            return f"Rapor biçimlendirme hatası: {str(e)}"


# =============================================================================
# ARAÇ FABRİKASI — Ajan türüne göre uygun araçları verir
# =============================================================================

def get_tools_for_agent(agent_name: str) -> list:
    """
    Ajan adına göre kullanabileceği araçları döndürür.

    NEDEN?
    Her ajanın farklı yeteneklere ihtiyacı var:
    - Araştırmacı ajanlar → arama aracı
    - Veri analistleri → veritabanı aracı
    - Rapor oluşturucular → formatlama aracı
    """
    tools_map = {
        "BehavioralAnalystAgent": [DatabaseQueryTool()],
        "AnomalyDetectorAgent": [DatabaseQueryTool()],
        "TherapyAdvisorAgent": [AutismResearchSearchTool()],
        "ReportGeneratorAgent": [ReportFormatterTool()],
        "ConversationalAgent": [AutismResearchSearchTool()],
        # Yeni ajanlar
        "LiteratureReviewAgent": [AutismResearchSearchTool()],
        "ParentSupportAgent": [AutismResearchSearchTool()],
        "DataAnalystAgent": [DatabaseQueryTool()],
    }
    return tools_map.get(agent_name, [])
