"""
AutiCare LangGraph State Management
Sistemin tümünü yönetmek için merkezi durum yönetimi sınıfı
"""

from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class AutiCareState(TypedDict):
    """
    AutiCare uygulamasının merkezi durum yönetimi
    
    Alanlar:
    - messages: Konuşma geçmişi ve tüm AI etkileşimleri
    - child_id: Çocuğun veritabanı ID'si
    - child_name: Çocuğun adı
    - parent_id: Ebeveynin ID'si
    - logs_data: Günlük davranış verileri
    - current_task: Mevcut görev türü ("report", "chat", "anomaly", "analysis")
    - current_query: Kullanıcı sorusu/isteği
    - task_status: Görev durumu ("pending", "processing", "completed", "error", "awaiting_review")
    - analysis_result: Davranış analizi sonucu
    - anomalies: Tespit edilen anormallikler
    - recommendations: Terapi önerileri
    - final_output: Son sonuç
    - error_message: Hata mesajı varsa
    - metadata: Ek veriler
    - should_end: İş akışı sonlanacak mı?
    
    YENİ ALANLAR (Modernizasyon):
    - search_results: Arama araçlarından dönen sonuçlar
    - literature_findings: Akademik araştırma bulguları
    - needs_human_review: İnsan onayı gerekiyor mu?
    - human_review_status: İnsan onayının durumu ("pending", "approved", "rejected", "modified")
    - human_review_notes: İnsan uzmanın notları
    - human_reviewed_output: İnsan tarafından düzenlenen çıktı
    - parallel_results: Paralel çalıştırılan görevlerin sonuçları
    - confidence_score: AI çıktısının güven skoru (0-1 arası)
    
    NOT: messages alanında `add` reducer KULLANILMIYOR çünkü tüm node'lar
    state'i in-place mutate edip tam state döndürüyor. add reducer ile bu
    yaklaşım mesaj duplikasyonuna sebep olur.
    """
    messages: List[BaseMessage]
    child_id: int
    child_name: str
    parent_id: int
    logs_data: Optional[List[Dict[str, Any]]]
    current_task: str  # "report", "chat", "anomaly", "analysis"
    current_query: Optional[str]
    task_status: str  # "pending", "processing", "completed", "error", "awaiting_review"
    analysis_result: Optional[Dict[str, Any]]
    anomalies: Optional[List[Dict[str, Any]]]
    recommendations: Optional[List[str]]
    final_output: Optional[str]
    error_message: Optional[str]
    metadata: Dict[str, Any]
    should_end: bool
    # Yeni alanlar — Agentic AI Modernizasyonu
    search_results: Optional[List[Dict[str, Any]]]
    literature_findings: Optional[str]
    needs_human_review: bool
    human_review_status: Optional[str]  # "pending", "approved", "rejected", "modified"
    human_review_notes: Optional[str]
    human_reviewed_output: Optional[str]
    parallel_results: Optional[Dict[str, Any]]
    confidence_score: Optional[float]


class TaskConfig(TypedDict):
    """Görev konfigürasyonu"""
    task_type: str
    description: str
    requires_analysis: bool
    requires_anomaly_detection: bool
    requires_recommendations: bool


# Desteklenen görev tipleri
SUPPORTED_TASKS = {
    "report": TaskConfig(
        task_type="report",
        description="Haftalık AI raporu oluştur",
        requires_analysis=True,
        requires_anomaly_detection=True,
        requires_recommendations=True
    ),
    "chat": TaskConfig(
        task_type="chat",
        description="Ebeveyn sorusunu yanıtla",
        requires_analysis=False,
        requires_anomaly_detection=False,
        requires_recommendations=False
    ),
    "anomaly": TaskConfig(
        task_type="anomaly",
        description="Anormal davranış tespiti",
        requires_analysis=True,
        requires_anomaly_detection=True,
        requires_recommendations=False
    ),
    "analysis": TaskConfig(
        task_type="analysis",
        description="Derinlemesine davranış analizi",
        requires_analysis=True,
        requires_anomaly_detection=False,
        requires_recommendations=True
    ),
    # YENİ GÖREV TÜRLERİ
    "deep_analysis": TaskConfig(
        task_type="deep_analysis",
        description="İstatistiksel derinlemesine veri analizi",
        requires_analysis=True,
        requires_anomaly_detection=True,
        requires_recommendations=True
    ),
    "literature_review": TaskConfig(
        task_type="literature_review",
        description="Güncel akademik kaynak araştırması",
        requires_analysis=False,
        requires_anomaly_detection=False,
        requires_recommendations=True
    ),
    "parent_support": TaskConfig(
        task_type="parent_support",
        description="Ebeveyn destek ve rehberlik",
        requires_analysis=False,
        requires_anomaly_detection=False,
        requires_recommendations=True
    ),
}


def init_state(
    child_id: int,
    child_name: str,
    parent_id: int,
    task_type: str,
    logs_data: Optional[List[Dict]] = None,
    query: Optional[str] = None,
) -> AutiCareState:
    """
    Yeni bir iş akışı için durum başlatır
    
    Args:
        child_id: Çocuk ID'si
        child_name: Çocuk adı
        parent_id: Ebeveyn ID'si
        task_type: Görev türü
        logs_data: İsteğe bağlı günlük verileri
        query: Ebeveynin sorusu (sohbet görevleri için)
    
    Returns:
        AutiCareState: Başlatılmış durum
    """
    return AutiCareState(
        messages=[],
        child_id=child_id,
        child_name=child_name,
        parent_id=parent_id,
        logs_data=logs_data or [],
        current_task=task_type,
        current_query=query,
        task_status="pending",
        analysis_result=None,
        anomalies=None,
        recommendations=None,
        final_output=None,
        error_message=None,
        metadata={
            "created_at": None,  # Workflow içinde ayarlanacak
            "processing_steps": [],
            "execution_time": 0,
        },
        should_end=False,
        # Yeni alanlar
        search_results=None,
        literature_findings=None,
        needs_human_review=False,
        human_review_status=None,
        human_review_notes=None,
        human_reviewed_output=None,
        parallel_results=None,
        confidence_score=None,
    )
