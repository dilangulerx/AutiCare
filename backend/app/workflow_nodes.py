"""
AutiCare LangGraph Workflow Nodes
LangGraph iş akışının tüm node'larını tanımlar
"""

import json
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.state import AutiCareState, SUPPORTED_TASKS

logger = logging.getLogger(__name__)


async def analyze_intent_node(state: AutiCareState) -> AutiCareState:
    """
    Node: Kullanıcı niyetini analiz et
    Hangi görev yapılması gerektiğini belirler
    
    Giriş: current_task, current_query
    Çıkış: Güncellenen messages, task_status
    """
    logger.info(f"🧠 Niyeti Analiz Etme: {state['current_task']}")
    
    task_type = state["current_task"]
    task_config = SUPPORTED_TASKS.get(task_type)
    
    if not task_config:
        state["error_message"] = f"Desteklenmeyen görev: {task_type}"
        state["task_status"] = "error"
        return state
    
    system_prompt = f"""
    Kullanıcı niyeti analiz ediliyor:
    - Çocuk: {state['child_name']} (ID: {state['child_id']})
    - Görev Türü: {task_config['description']}
    - İstek: {state.get('current_query', 'Otomatik görev')}
    
    Buna göre uygun CrewAI görevlerini belirle.
    """
    
    # Durum için sistem mesajı ekle
    state["messages"].append(SystemMessage(content=system_prompt))
    state["task_status"] = "processing"
    state["metadata"]["processing_steps"].append("intent_analysis")
    
    logger.info(f"✓ Niyeti Analiz Tamamlandı: {task_config['description']}")
    
    return state


async def prepare_crew_tasks_node(state: AutiCareState) -> AutiCareState:
    """
    Node: CrewAI Görevlerini Hazırla
    Gerekli CrewAI agent görevlerini başlatmaya hazırla
    
    Giriş: current_task, logs_data
    Çıkış: Güncellenen task_status, metadata
    """
    logger.info(f"🤖 CrewAI Görevleri Hazırlanıyor: {state['current_task']}")
    
    task_config = SUPPORTED_TASKS.get(state["current_task"])
    if not task_config:
        return state
    
    crew_tasks = []
    
    # Analiz gerekiyorsa
    if task_config["requires_analysis"]:
        crew_tasks.append({
            "agent": "BehavioralAnalystAgent",
            "task": "analyze_logs_task",
            "priority": 1
        })
    
    # Anomali tespiti gerekiyorsa
    if task_config["requires_anomaly_detection"]:
        crew_tasks.append({
            "agent": "AnomalyDetectorAgent",
            "task": "detect_anomalies_task",
            "priority": 1
        })
    
    # Öneriler gerekiyorsa
    if task_config["requires_recommendations"]:
        crew_tasks.append({
            "agent": "TherapyAdvisorAgent",
            "task": "generate_recommendations_task",
            "priority": 2
        })
    
    # Rapor görevleri için
    if state["current_task"] == "report":
        crew_tasks.append({
            "agent": "ReportGeneratorAgent",
            "task": "compile_weekly_report_task",
            "priority": 3
        })
    
    # Sohbet görevleri için
    if state["current_task"] == "chat":
        crew_tasks.append({
            "agent": "ConversationalAgent",
            "task": "handle_chat_query_task",
            "priority": 1
        })
    
    state["metadata"]["crew_tasks"] = crew_tasks
    state["metadata"]["processing_steps"].append("crew_preparation")
    
    logger.info(f"✓ {len(crew_tasks)} CrewAI Görevi Hazırlandı")
    
    return state


async def execute_crew_tasks_node(state: AutiCareState) -> AutiCareState:
    """
    Node: CrewAI Görevlerini Yürüt
    CrewAI ile beraber önceden tanımlanmış görevleri çalıştır
    
    Not: Gerçek CrewAI entegrasyonu controllers/routers'da yapılacak
    Bu node hazırlık ve koordinasyon işini yapar
    
    Giriş: metadata.crew_tasks, logs_data
    Çıkış: analysis_result, anomalies, recommendations
    """
    logger.info(f"🚀 CrewAI Görevleri Yürütülüyor")
    
    crew_tasks = state["metadata"].get("crew_tasks", [])
    
    if not crew_tasks:
        logger.warning("⚠️ Çalıştırılacak CrewAI görevi yok")
        state["task_status"] = "completed"
        return state
    
    # Görevleri öncelik sırasına göre sırala
    sorted_tasks = sorted(crew_tasks, key=lambda x: x.get("priority", 0))
    
    state["metadata"]["crew_tasks_ordered"] = sorted_tasks
    state["metadata"]["processing_steps"].append("crew_execution")
    
    # Görev mesajı ekle
    task_summary = "\n".join([f"- {t['task']} ({t['agent']})" for t in sorted_tasks])
    state["messages"].append(
        HumanMessage(content=f"CrewAI Görevleri Başlatılıyor:\n{task_summary}")
    )
    
    logger.info(f"✓ {len(sorted_tasks)} Görevi Yürütmeye Hazır")
    
    return state


async def process_analysis_results_node(state: AutiCareState) -> AutiCareState:
    """
    Node: Analiz Sonuçlarını İşle
    CrewAI sonuçlarını işle ve durum güncelle
    
    Giriş: CrewAI sonuçları (analysis_result, anomalies, recommendations)
    Çıkış: Son kurulu durum
    """
    logger.info(f"📊 Analiz Sonuçları İşleniyor")
    
    # Analiz sonuçları varsa log'la
    if state.get("analysis_result"):
        state["messages"].append(
            AIMessage(content=f"Analiz Tamamlandı: {json.dumps(state['analysis_result'], ensure_ascii=False)}")
        )
    
    # Anomaliler varsa uyarı
    if state.get("anomalies"):
        state["messages"].append(
            AIMessage(content=f"⚠️ Anormallikler Tespit Edildi: {len(state['anomalies'])} anormallik")
        )
    
    # Öneriler varsa ekle
    if state.get("recommendations"):
        state["messages"].append(
            AIMessage(content=f"💡 Öneriler Oluşturuldu: {len(state['recommendations'])} öneri")
        )
    
    state["metadata"]["processing_steps"].append("results_processing")
    state["task_status"] = "completed"
    
    logger.info(f"✓ Analiz Sonuçları İşlendi")
    
    return state


async def generate_final_output_node(state: AutiCareState) -> AutiCareState:
    """
    Node: Son Çıktıyı Oluştur
    Tüm bilgileri derleyerek son çıktıyı hazırla
    
    Giriş: analysis_result, anomalies, recommendations
    Çıkış: final_output, should_end
    """
    logger.info(f"📝 Son Çıktı Oluşturulıyor")
    
    output_parts = []
    
    # Başlık ekle
    task_type = state["current_task"]
    output_parts.append(f"=== {state['child_name']} için {task_type.upper()} Raporu ===\n")
    
    # Analiz sonuçları
    if state.get("analysis_result"):
        output_parts.append(f"📊 Analiz Sonuçları:\n{json.dumps(state['analysis_result'], ensure_ascii=False, indent=2)}\n")
    
    # Anormallikler
    if state.get("anomalies"):
        output_parts.append(f"⚠️ Tespit Edilen Anormallikler ({len(state['anomalies'])} adet):")
        for i, anomaly in enumerate(state["anomalies"], 1):
            output_parts.append(f"  {i}. {anomaly.get('description', 'Anomali')}")
        output_parts.append("")
    
    # Öneriler
    if state.get("recommendations"):
        output_parts.append(f"💡 Terapi Önerileri ({len(state['recommendations'])} adet):")
        for i, rec in enumerate(state["recommendations"], 1):
            output_parts.append(f"  {i}. {rec}")
        output_parts.append("")
    
    # Zaman bilgisi
    output_parts.append(f"⏱️ İşlem Zamanı: {datetime.now().isoformat()}")
    
    state["final_output"] = "\n".join(output_parts)
    state["metadata"]["processing_steps"].append("final_generation")
    state["should_end"] = True
    
    logger.info(f"✓ Son Çıktı Oluşturuldu ({len(output_parts)} parça)")
    
    return state


async def error_handling_node(state: AutiCareState) -> AutiCareState:
    """
    Node: Hata İşleme
    Hataları yakala ve uygun şekilde rapkala
    
    Giriş: error_message varsa
    Çıkış: Düzeltilmiş durum veya sonlandırma
    """
    if state.get("error_message"):
        logger.error(f"❌ Hata Tespit Edildi: {state['error_message']}")
        
        error_output = f"""
⚠️ İşlem Sırasında Hata Oluştu
---------------------------------
Çocuk: {state['child_name']} (ID: {state['child_id']})
Görev: {state['current_task']}
Hata: {state['error_message']}
Zaman: {datetime.now().isoformat()}

Lütfen yöneticinize başvurun.
        """.strip()
        
        state["final_output"] = error_output
        state["messages"].append(
            AIMessage(content=f"❌ Hata: {state['error_message']}")
        )
    
    state["metadata"]["processing_steps"].append("error_handling")
    state["should_end"] = True
    
    return state


# Node Tanımları Sözlüğü
WORKFLOW_NODES = {
    "analyze_intent": analyze_intent_node,
    "prepare_crew_tasks": prepare_crew_tasks_node,
    "execute_crew_tasks": execute_crew_tasks_node,
    "process_analysis": process_analysis_results_node,
    "generate_output": generate_final_output_node,
    "error_handling": error_handling_node,
}
