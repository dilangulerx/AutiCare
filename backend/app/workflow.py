"""
AutiCare LangGraph Workflow Graph
Tüm node'ları bir iş akışına bağlar ve sürecin akışını yönetir
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
)

logger = logging.getLogger(__name__)


def create_auticare_workflow():
    """
    AutiCare Hibrit AI İş Akışını Oluştur
    LangGraph + CrewAI entegrasyonlu iş akışını yapılandırır
    
    Akış:
    START 
      → analyze_intent (Niyeti Analiz Et)
      → prepare_crew_tasks (CrewAI Görevlerini Hazırla)
      → execute_crew_tasks (CrewAI'ı Çalıştır)
      → process_analysis (Sonuçları İşle)
      → generate_output (Çıktıyı Oluştur)
      → END
    
    ERROR HANDLING:
      Herhangi bir aşamada hata → error_handling → END
    
    Returns:
        StateGraph: Derlenmiş iş akışı
    """
    
    workflow = StateGraph(AutiCareState)
    
    # Node'ları ekle
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("prepare_crew_tasks", prepare_crew_tasks_node)
    workflow.add_node("execute_crew_tasks", execute_crew_tasks_node)
    workflow.add_node("process_analysis", process_analysis_results_node)
    workflow.add_node("generate_output", generate_final_output_node)
    
    # Edge'leri (bağlantıları) ekle
    workflow.add_edge(START, "analyze_intent")
    workflow.add_edge("analyze_intent", "prepare_crew_tasks")
    workflow.add_edge("prepare_crew_tasks", "execute_crew_tasks")
    workflow.add_edge("execute_crew_tasks", "process_analysis")
    workflow.add_edge("process_analysis", "generate_output")
    workflow.add_edge("generate_output", END)
    
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
                # Gerçek zamanlı akış sonuçlarını al
                result_state = None
                for event in self.workflow.stream(state):
                    logger.debug(f"📡 Streaming Event: {event}")
                    result_state = event
                final_state = result_state
            else:
                # Tamamlanmış sonucu al
                final_state = self.workflow.invoke(state)
            
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
                "messages": [msg.dict() for msg in final_state.get("messages", [])],
                "metadata": final_state.get("metadata", {}),
                "error": final_state.get("error_message"),
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
            "version": "1.0.0",
            "framework": "LangGraph + CrewAI",
            "description": "LangGraph orchestration ile CrewAI agent yönetim sistemi",
            "nodes": [
                "analyze_intent",
                "prepare_crew_tasks",
                "execute_crew_tasks",
                "process_analysis",
                "generate_output",
                "error_handling",
            ],
            "supported_tasks": ["report", "chat", "anomaly", "analysis"],
        }


# Global Executor instance'ı
_executor = None


def get_workflow_executor() -> AutiCareWorkflowExecutor:
    """Global executor'u al veya oluştur"""
    global _executor
    if _executor is None:
        _executor = AutiCareWorkflowExecutor()
    return _executor
