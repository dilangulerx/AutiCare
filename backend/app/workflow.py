"""
AutiCare LangGraph Workflow Graph
Tüm node'ları bir iş akışına bağlar ve sürecin akışını yönetir.

MODERNIZASYON (v2.0):
- Dinamik rota belirleme: Görev türüne göre farklı yollara dallanma
- Arama düğümü: Dış kaynaklardan bilgi toplama
- Human-in-the-Loop: Kritik çıktılar için insan onay mekanizması
- Koşullu dallanma: route_by_intent, route_after_analysis, route_after_review

İŞ AKIŞI GRAFİĞİ:
START
  → analyze_intent
  → [DİNAMİK ROTA]
     ├─ search_information → prepare_crew_tasks  (araştırma gerektiren görevler)
     └─ prepare_crew_tasks                       (hızlı yanıt görevleri)
  → execute_crew_tasks
  → process_analysis
  → [DİNAMİK ROTA]
     ├─ human_review → [ROTA] → generate_output  (kritik görevler)
     └─ generate_output                           (rutin görevler)
  → END
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

from langgraph.graph import StateGraph, START, END
from app.state import AutiCareState, init_state
from app.workflow_nodes import (
    analyze_intent_node,
    prepare_crew_tasks_node,
    execute_crew_tasks_node,
    process_analysis_results_node,
    generate_final_output_node,
    error_handling_node,
    # Yeni node'lar
    search_information_node,
    human_review_node,
    # Rota fonksiyonları
    route_by_intent,
    route_after_analysis,
    route_after_review,
)

logger = logging.getLogger(__name__)


def create_auticare_workflow():
    """
    AutiCare Hibrit AI İş Akışını Oluştur (v2.0)
    
    NEDEN BU YENİ YAPI?
    Eski iş akışı sıralı (lineer) bir yapıdaydı — her görev aynı yoldan geçiyordu.
    Yeni yapı koşullu dallanma (conditional edges) kullanarak:
    
    1. HIZLI YANIT: Chat görevleri arama yapmadan doğrudan crew'a gider
    2. DERİN ANALİZ: Araştırma gerektiren görevler önce search → sonra crew
    3. GÜVENLİK: Kritik çıktılar insan onayından geçer
    4. ADAPTİF: Veri miktarına göre farklı yollar seçilir
    
    Returns:
        StateGraph: Derlenmiş iş akışı
    """
    
    workflow = StateGraph(AutiCareState)
    
    # ─── TÜM NODE'LARI EKLE ───
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("search_information", search_information_node)
    workflow.add_node("prepare_crew_tasks", prepare_crew_tasks_node)
    workflow.add_node("execute_crew_tasks", execute_crew_tasks_node)
    workflow.add_node("process_analysis", process_analysis_results_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("generate_output", generate_final_output_node)
    workflow.add_node("error_handling", error_handling_node)
    
    # ─── EDGE'LER (BAĞLANTILAR) ───
    
    # Başlangıç → Niyet Analizi
    workflow.add_edge(START, "analyze_intent")
    
    # Niyet Analizi → DİNAMİK ROTA
    # NEDEN: Görev türüne göre arama gerekip gerekmediğini belirler
    workflow.add_conditional_edges(
        "analyze_intent",
        route_by_intent,
        {
            "search_information": "search_information",
            "prepare_crew_tasks": "prepare_crew_tasks",
            "error_handling": "error_handling",
        }
    )
    
    # Arama → CrewAI Görev Hazırlığı
    workflow.add_edge("search_information", "prepare_crew_tasks")
    
    # CrewAI Hazırlık → CrewAI Çalıştırma
    workflow.add_edge("prepare_crew_tasks", "execute_crew_tasks")
    
    # CrewAI Çalıştırma → Sonuç İşleme
    workflow.add_edge("execute_crew_tasks", "process_analysis")
    
    # Sonuç İşleme → DİNAMİK ROTA (HITL veya doğrudan çıktı)
    # NEDEN: Kritik görevler insan onayından geçmeli, rutin görevler doğrudan çıktıya
    workflow.add_conditional_edges(
        "process_analysis",
        route_after_analysis,
        {
            "human_review": "human_review",
            "generate_output": "generate_output",
        }
    )
    
    # İnsan Onayı → DİNAMİK ROTA
    # NEDEN: Reddedilen çıktılar yeniden işlenmeli
    workflow.add_conditional_edges(
        "human_review",
        route_after_review,
        {
            "generate_output": "generate_output",
            "prepare_crew_tasks": "prepare_crew_tasks",
        }
    )
    
    # Son Çıktı → BİTİŞ
    workflow.add_edge("generate_output", END)
    
    # Hata İşleme → BİTİŞ
    workflow.add_edge("error_handling", END)
    
    return workflow.compile()


class AutiCareWorkflowExecutor:
    """
    AutiCare İş Akışı Yöneticisi
    LangGraph workflow'unu çalıştırır ve yönetir
    """
    
    def __init__(self):
        """Executor'ı başlat"""
        self.workflow = create_auticare_workflow()
        logger.info("✓ AutiCare Workflow Executor başlatıldı")
    
    async def execute(
        self,
        child_id: int,
        child_name: str,
        parent_id: int,
        task_type: str,
        logs_data: Optional[List[Dict[str, Any]]] = None,
        query: Optional[str] = None,
        streaming: bool = False,
    ) -> Dict[str, Any]:
        """
        İş Akışını Çalıştır
        
        Args:
            child_id: Çocuk ID'si
            child_name: Çocuk adı
            parent_id: Ebeveyn ID'si
            task_type: Görev türü ("report", "chat", "anomaly", "analysis")
            logs_data: İsteğe bağlı davranış verileri
            query: İsteğe bağlı sohbet sorgusu
            streaming: Sonuçlar gerçek zamanlı mı akışık mı?
        
        Returns:
            Dict: İş akışı sonuçları
        """
        
        logger.info(f"🚀 İş Akışı Başlatılıyor: {task_type} ({child_name})")
        
        # Başlangıç durumunu hazırla
        state = init_state(
            child_id=child_id,
            child_name=child_name,
            parent_id=parent_id,
            task_type=task_type,
            logs_data=logs_data,
            query=query,
        )
        
        # Metadata başlat
        state["metadata"]["created_at"] = datetime.now().isoformat()
        state["metadata"]["streaming"] = streaming
        
        start_time = datetime.now()
        
        try:
            # İş akışını çalıştır
            if streaming:
                # Gerçek zamanlı akış — astream() async generator döndürür
                final_state = None
                async for event in self.workflow.astream(state):
                    logger.debug(f"📡 Streaming Event: {list(event.keys())}")
                    for node_name, node_output in event.items():
                        if isinstance(node_output, dict):
                            if final_state is None:
                                final_state = dict(state)
                            final_state.update(node_output)
                if final_state is None:
                    final_state = state
            else:
                # Tamamlanmış sonucu al — ainvoke() event loop'u bloklamaz
                final_state = await self.workflow.ainvoke(state)
            
            # Yürütme zamanını hesapla
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            final_state["metadata"]["execution_time"] = execution_time
            
            logger.info(f"✓ İş Akışı Tamamlandı ({execution_time:.2f}s)")
            
            return {
                "success": True,
                "status": final_state.get("task_status", "completed"),
                "output": final_state.get("final_output", ""),
                "analysis": final_state.get("analysis_result"),
                "anomalies": final_state.get("anomalies"),
                "recommendations": final_state.get("recommendations"),
                "messages": [
                    msg.model_dump() if hasattr(msg, 'model_dump') else msg.dict()
                    for msg in final_state.get("messages", [])
                ],
                "metadata": final_state.get("metadata", {}),
                "error": final_state.get("error_message"),
                # Yeni alanlar
                "needs_human_review": final_state.get("needs_human_review", False),
                "human_review_status": final_state.get("human_review_status"),
                "confidence_score": final_state.get("confidence_score"),
                "search_results": final_state.get("search_results"),
                "literature_findings": final_state.get("literature_findings"),
            }
        
        except Exception as e:
            logger.error(f"❌ İş Akışı Hatasısı: {str(e)}", exc_info=True)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                "success": False,
                "status": "error",
                "output": "",
                "error": str(e),
                "execution_time": execution_time,
                "metadata": {"created_at": state["metadata"]["created_at"]},
            }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Workflow bilgilerini al"""
        return {
            "name": "AutiCare Hibrit AI İş Akışı",
            "version": "2.0.0",
            "framework": "LangGraph + CrewAI",
            "description": "Dinamik rota, arama entegrasyonu ve HITL destekli LangGraph + CrewAI hibrit sistem",
            "nodes": [
                "analyze_intent",
                "search_information",
                "prepare_crew_tasks",
                "execute_crew_tasks",
                "process_analysis",
                "human_review",
                "generate_output",
                "error_handling",
            ],
            "supported_tasks": [
                "report", "chat", "anomaly", "analysis",
                "deep_analysis", "literature_review", "parent_support",
            ],
            "features": [
                "dynamic_routing",
                "search_integration",
                "human_in_the_loop",
                "confidence_scoring",
            ],
        }


# Global Executor instance'ı
_executor = None


def get_workflow_executor() -> AutiCareWorkflowExecutor:
    """Global executor'u al veya oluştur"""
    global _executor
    if _executor is None:
        _executor = AutiCareWorkflowExecutor()
    return _executor
