"""
AutiCare LangGraph Workflow Nodes
LangGraph iş akışının tüm node'larını tanımlar.

MODERNIZASYON:
- search_information_node: Dış kaynaklardan bilgi toplama
- human_review_node: İnsan-döngüde (HITL) onay mekanizması
- Dinamik rota belirleme: route_by_intent ve route_after_analysis
- Güven skoru hesaplama
"""

import json
import asyncio
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
    - Kullanıcı Rolü: {state.get('user_role', 'parent')}
    
    Çok Önemli Kural: Eğer kullanıcı rolü 'parent' (ebeveyn) ise KESİNLİKLE tıbbi tavsiye veya ilaç önerisi verme. Sadece günlük rutine dayalı zararsız tavsiyeler ver. Eğer rol 'admin' (uzman) ise bilimsel tıbbi/ilaç önerileri verebilirsin.
    
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
    
    # Deep analysis görevleri için
    if state["current_task"] == "deep_analysis":
        crew_tasks.append({
            "agent": "DataAnalystAgent",
            "task": "deep_data_analysis_task",
            "priority": 1
        })
        crew_tasks.append({
            "agent": "TherapyAdvisorAgent",
            "task": "search_enhanced_recommendations_task",
            "priority": 2
        })
    
    # Literatür araştırması görevleri için
    if state["current_task"] == "literature_review":
        crew_tasks.append({
            "agent": "LiteratureReviewAgent",
            "task": "literature_review_task",
            "priority": 1
        })
        crew_tasks.append({
            "agent": "TherapyAdvisorAgent",
            "task": "search_enhanced_recommendations_task",
            "priority": 2
        })
    
    # Ebeveyn destek görevleri için
    if state["current_task"] == "parent_support":
        crew_tasks.append({
            "agent": "ParentSupportAgent",
            "task": "parent_guidance_task",
            "priority": 1
        })
        crew_tasks.append({
            "agent": "ConversationalAgent",
            "task": "handle_chat_query_task",
            "priority": 2
        })
    
    state["metadata"]["crew_tasks"] = crew_tasks
    state["metadata"]["processing_steps"].append("crew_preparation")
    
    logger.info(f"✓ {len(crew_tasks)} CrewAI Görevi Hazırlandı")
    
    return state


async def execute_crew_tasks_node(state: AutiCareState) -> AutiCareState:
    """
    Node: CrewAI Görevlerini Yürüt
    CrewAI ekiplerini gerçekten çalıştırır ve sonuçları state'e yazar.
    
    Giriş: metadata.crew_tasks, logs_data, current_task
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
    
    task_summary = "\n".join([f"- {t['task']} ({t['agent']})" for t in sorted_tasks])
    state["messages"].append(
        HumanMessage(content=f"CrewAI Görevleri Başlatılıyor:\n{task_summary}")
    )
    
    # ── GERÇEK CREWAI ÇALIŞTIRMASI ──
    try:
        from app.crew_manager import get_crew_manager
        
        manager = get_crew_manager()
        
        # logs_data'yı metin formatına dönüştür (CrewAI için)
        logs_data = state.get("logs_data") or []
        logs_text = "\n".join([
            f"[{log.get('date', '?')}] Göz İletişimi: {log.get('eye_contact', '?')}, "
            f"İletişim: {log.get('communication_score', '?')}, "
            f"Aggresyon: {log.get('aggression_level', '?')}, "
            f"Uyku: {log.get('sleep_hours', '?')}s, "
            f"Not: {log.get('behavioral_notes', log.get('notes', 'Yok'))}"
            for log in logs_data
        ])
        
        if not logs_text:
            logs_text = "Henüz günlük verisi yok."
        
        crew_type = state["current_task"]
        result = await manager.execute_crew(
            crew_type=crew_type,
            child_name=state["child_name"],
            logs_text=logs_text,
            query=state.get("current_query"),
            user_role=state.get("user_role", "parent"),
        )
        
        if result.get("success"):
            crew_output = result.get("output", "")
            
            # Çıktıyı state alanlarına parse et
            state["analysis_result"] = {
                "crew_type": crew_type,
                "raw_output": crew_output,
                "tasks_executed": result.get("tasks_executed", 0),
                "agents_used": result.get("agents_used", 0),
            }
            
            state["messages"].append(
                AIMessage(content=f"✓ CrewAI tamamlandı: {result.get('tasks_executed', 0)} görev çalıştırıldı.")
            )
            logger.info(f"✓ CrewAI başarılı: {crew_type}")
        else:
            error_msg = result.get("error", "Bilinmeyen hata")
            state["error_message"] = f"CrewAI hatası: {error_msg}"
            state["messages"].append(
                AIMessage(content=f"❌ CrewAI hatası: {error_msg}")
            )
            logger.error(f"❌ CrewAI başarısız: {error_msg}")
    
    except Exception as e:
        logger.error(f"❌ CrewAI çalıştırma hatası: {e}", exc_info=True)
        state["error_message"] = f"CrewAI çalıştırma hatası: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"❌ CrewAI çalıştırılamadı: {str(e)}")
        )
    
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
    
    # Başlık
    task_type = state["current_task"]
    
    # Sohbet ve destek görevlerinde sade yanıt döndür
    if task_type in ("chat", "parent_support"):
        output = ""
        if state.get("human_reviewed_output"):
            output = state["human_reviewed_output"]
        elif state.get("analysis_result"):
            output = state["analysis_result"].get("raw_output") or state["analysis_result"].get("output") or str(state["analysis_result"])
            
        if state.get("human_review_notes"):
            output = f"👤 Uzman Notu: {state['human_review_notes']}\n\n{output}"
            
        state["final_output"] = output
        state["metadata"]["processing_steps"].append("final_generation")
        state["should_end"] = True
        logger.info(f"✓ Chat çıktısı oluşturuldu")
        return state
        
    output_parts.append(f"=== {state['child_name']} için {task_type.upper()} Raporu ===\n")
    
    # İnsan onayı durumunu
    if state.get("needs_human_review"):
        review_status = state.get("human_review_status", "pending")
        if review_status == "pending":
            output_parts.append(f"⏳ İnsan Onayı: Bekleniyor (Güven: {state.get('confidence_score', 0):.0%})\n")
        elif review_status == "approved":
            output_parts.append(f"✅ İnsan Onayı: Onaylandı\n")
        elif review_status == "modified":
            output_parts.append(f"✏️ İnsan Onayı: Düzenlendi\n")
        elif review_status == "rejected":
            output_parts.append(f"❌ İnsan Onayı: Reddedildi\n")
    
    # Analiz sonuçları
    if state.get("analysis_result"):
        if isinstance(state["analysis_result"], dict) and "output" in state["analysis_result"]:
            output_parts.append(f" Analiz Sonuçları:\n{state['analysis_result']['output']}\n")
        elif isinstance(state["analysis_result"], dict) and "raw_output" in state["analysis_result"]:
            output_parts.append(f" Analiz Sonuçları:\n{state['analysis_result']['raw_output']}\n")
        else:
            output_parts.append(f" Analiz Sonuçları:\n{json.dumps(state['analysis_result'], ensure_ascii=False, indent=2)}\n")
    
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
    
    # Literatür bulguları
    if state.get("literature_findings"):
        output_parts.append(f"📚 Araştırma Bulguları:")
        output_parts.append(state["literature_findings"][:1000])
        output_parts.append("")
    
    # İnsan notları
    if state.get("human_review_notes"):
        output_parts.append(f"👤 Uzman Notları:")
        output_parts.append(state["human_review_notes"])
        output_parts.append("")
    
    # İnsan tarafından düzenlenen çıktı varsa ana çıktıyı değiştir
    if state.get("human_reviewed_output"):
        output_parts.append(f"📋 Uzman Düzeltmeli Çıktı:")
        output_parts.append(state["human_reviewed_output"])
        output_parts.append("")
    
    # Güven skoru
    if state.get("confidence_score") is not None:
        output_parts.append(f"🎯 Güven Skoru: {state['confidence_score']:.0%}")
    
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


# =============================================================================
# YENİ NODE'LAR — Agentic AI Modernizasyonu
# =============================================================================

async def search_information_node(state: AutiCareState) -> AutiCareState:
    """
    Node: Dış Kaynaklardan Bilgi Toplama
    
    NEDEN BU NODE?
    Mevcut ajanlar sadece logs_data ile sınırlıydı. Bu node, ajanların
    karar vermeden önce güncel terapi bilgilerini, akademik kaynakları
    ve en iyi uygulamaları internetten aramasını sağlar.
    
    NE ZAMAN TETİKLENİR?
    - report ve deep_analysis görevlerinde otomatik olarak
    - literature_review görevinde birincil olarak
    - logs_data yetersiz olduğunda (< 3 kayıt)
    """
    logger.info(f"🔍 Bilgi Araştırması Başlatılıyor: {state['current_task']}")
    
    try:
        from app.tools import AutismResearchSearchTool
        
        search_tool = AutismResearchSearchTool()
        search_queries = []
        
        # Görev türüne göre arama sorguları oluştur
        task = state["current_task"]
        child_name = state["child_name"]
        
        if task in ("report", "deep_analysis", "chat"):
            search_queries.append(f"autism behavioral intervention strategies children")
            if task == "chat" and state.get("current_query"):
                search_queries.append(f"autism {state['current_query']} therapy recommendations")
            # Anomali varsa spesifik arama
            if state.get("anomalies"):
                for anomaly in state["anomalies"][:2]:
                    desc = anomaly.get("description", "")
                    if desc:
                        search_queries.append(f"autism {desc} intervention")
        
        elif task == "literature_review":
            search_queries.append("autism spectrum disorder latest research 2024 2025")
            search_queries.append("evidence-based autism therapy techniques")
        
        elif task == "parent_support":
            search_queries.append("autism parent coping strategies support")
        
        # Logs_data yetersizse ek arama
        logs = state.get("logs_data") or []
        if len(logs) < 3:
            search_queries.append("autism daily behavior tracking best practices")
        
        # Aramaları çalıştır
        all_results = []
        for query in search_queries[:3]:  # Maks 3 arama
            try:
                result = await asyncio.to_thread(search_tool._run, query)
                if result and "hata" not in result.lower():
                    all_results.append({"query": query, "results": result})
            except Exception as e:
                logger.warning(f"Arama hatası ({query}): {e}")
        
        state["search_results"] = all_results
        
        # Literatür bulgularını özetle
        if all_results:
            findings = "\n\n".join([
                f"Araştırma: {r['query']}\n{r['results'][:500]}"
                for r in all_results
            ])
            state["literature_findings"] = findings
            state["messages"].append(
                AIMessage(content=f"🔍 {len(all_results)} araştırma sonucu toplandı.")
            )
        
        state["metadata"]["processing_steps"].append("search_information")
        logger.info(f"✓ {len(all_results)} araştırma sonucu toplandı")
        
    except Exception as e:
        logger.warning(f"⚠️ Arama düğümü hatası: {e}")
        state["search_results"] = []
        state["literature_findings"] = None
    
    return state


async def human_review_node(state: AutiCareState) -> AutiCareState:
    """
    Node: İnsan-Döngüde (Human-in-the-Loop) Onay Mekanizması
    
    NEDEN BU NODE?
    AI tarafından üretilen kritik çıktılar (terapi önerileri, anomali uyarıları)
    bir insan uzman tarafından gözden geçirilmeli. Bu, güvenilirliği artırır,
    yanlış pozitif/negatifleri azaltır ve tıbbi güvenlik sağlar.
    
    ÇALIŞMA PRENSİBİ:
    1. Güven skoru hesaplanır (veri miktarı, anomali ciddiyet seviyesi vb.)
    2. Güven skoru eşik değerinin altındaysa → insan onayı gerekir
    3. İş akışı "awaiting_review" durumuna geçer
    4. İnsan onayı/reddi/düzeltmesi alındığında akış devam eder
    """
    logger.info(f"👤 İnsan Onayı Değerlendirmesi")
    
    # Güven skoru hesapla
    confidence = _calculate_confidence_score(state)
    state["confidence_score"] = confidence
    
    # Hangi durumlarda insan onayı gerekir?
    CONFIDENCE_THRESHOLD = 0.7
    CRITICAL_TASKS = {"report", "anomaly", "deep_analysis"}
    
    needs_review = (
        confidence < CONFIDENCE_THRESHOLD
        or state["current_task"] in CRITICAL_TASKS
        or (state.get("anomalies") and len(state["anomalies"]) > 0)
    )
    
    if needs_review:
        state["needs_human_review"] = True
        state["human_review_status"] = "pending"
        state["task_status"] = "awaiting_review"
        
        review_summary = {
            "confidence_score": confidence,
            "task_type": state["current_task"],
            "child_name": state["child_name"],
            "anomaly_count": len(state.get("anomalies") or []),
            "recommendation_count": len(state.get("recommendations") or []),
            "reason": _get_review_reason(confidence, state),
        }
        state["metadata"]["review_summary"] = review_summary

        state["messages"].append(
            AIMessage(content=f"👤 İnsan onayı bekleniyor (Güven: {confidence:.0%}). Sebep: {review_summary['reason']}")
        )
        
        logger.info(f"⏸️ İnsan onayı gerekiyor (güven: {confidence:.0%})")
    else:
        state["needs_human_review"] = False
        state["human_review_status"] = "auto_approved"
        
        state["messages"].append(
            AIMessage(content=f"✅ Otomatik onay (Güven: {confidence:.0%})")
        )
        
        logger.info(f"✅ Otomatik onay (güven: {confidence:.0%})")
    
    state["metadata"]["processing_steps"].append("human_review")
    
    return state


def _calculate_confidence_score(state: AutiCareState) -> float:
    """
    AI çıktısının güven skorunu hesapla (0.0-1.0 arası).
    
    NEDEN?
    Güven skoru, HITL mekanizmasının otomatik onay mı yoksa insan müdahalesi mi
    gerektirdiğini belirler. Düşük güven = insan onayı gerekir.
    
    FAKTÖRLER:
    - Veri miktarı (daha fazla veri = daha yüksek güven)
    - Anomali sayısı (daha az anomali = daha yüksek güven)
    - Arama sonuçları (kaynak bulunması güveni artırır)
    """
    score = 0.5  # Başlangıç
    
    # Veri miktarı etkisi
    logs = state.get("logs_data") or []
    if len(logs) >= 14:
        score += 0.2
    elif len(logs) >= 7:
        score += 0.1
    elif len(logs) < 3:
        score -= 0.15
    
    # Anomali etkisi
    anomalies = state.get("anomalies") or []
    if len(anomalies) == 0:
        score += 0.1
    elif len(anomalies) > 3:
        score -= 0.15
    
    # Arama sonuçları etkisi
    if state.get("search_results"):
        score += 0.1
    
    # Analiz sonucu var mı?
    if state.get("analysis_result"):
        score += 0.1
    
    return max(0.0, min(1.0, score))


def _get_review_reason(confidence: float, state: AutiCareState) -> str:
    """İnsan onayı gerekçesini belirle"""
    reasons = []
    
    if confidence < 0.5:
        reasons.append("Düşük güven skoru")
    
    logs = state.get("logs_data") or []
    if len(logs) < 3:
        reasons.append("Yetersiz veri")
    
    anomalies = state.get("anomalies") or []
    if len(anomalies) > 3:
        reasons.append(f"{len(anomalies)} anomali tespit edildi")
    
    if state["current_task"] in ("report", "anomaly", "deep_analysis"):
        reasons.append("Kritik görev türü")
    
    return "; ".join(reasons) if reasons else "Rutin gözden geçirme"


# =============================================================================
# DİNAMİK ROTA BELİRLEME FONKSİYONLARI
# =============================================================================

def route_by_intent(state: AutiCareState) -> str:
    """
    Dinamik Rota Belirleme — Niyet Analizi Sonrasında
    
    NEDEN?
    Mevcut sistemde tüm görevler aynı sıralı yoldan geçiyordu.
    Bu fonksiyon, görev türüne göre farklı yollara yönlendirme yapar:
    - Hata varsa → error_handling
    - Araştırma gerektiren görevler → search_information → crew
    - Chat görevleri → doğrudan crew (daha hızlı yanıt)
    """
    # Hata durumu kontrolü
    if state.get("task_status") == "error" or state.get("error_message"):
        return "error_handling"
    
    task = state["current_task"]
    logs = state.get("logs_data") or []
    
    # Araştırma gerektiren görevler
    if task in ("literature_review", "deep_analysis", "chat"):
        return "search_information"
    
    # Rapor görevi — yetersiz veri varsa araştır
    if task == "report" and len(logs) < 5:
        return "search_information"
    
    # Diğer görevler — standart yol
    return "prepare_crew_tasks"


def route_after_analysis(state: AutiCareState) -> str:
    """
    Analiz Sonrası Rota Belirleme
    
    NEDEN?
    Analiz sonucuna göre insan onayına mı yoksa doğrudan çıktıya mı
    gidileceğini belirler. Kritik bulgular → HITL, rutin sonuçlar → çıktı.
    """
    # Kritik görevler her zaman insan onayından geçer
    if state["current_task"] in ("report", "anomaly", "deep_analysis"):
        return "human_review"
    
    # Anomali tespit edildiyse insan onayı
    anomalies = state.get("anomalies") or []
    if len(anomalies) > 0:
        return "human_review"
    
    return "generate_output"


def route_after_review(state: AutiCareState) -> str:
    """
    İnsan Onayı Sonrası Rota Belirleme
    
    NEDEN?
    Reddedilen çıktılar düzeltilmeli, onaylananlar doğrudan çıktıya gider.
    """
    review_status = state.get("human_review_status", "pending")
    
    if review_status == "pending":
        # Hala onay bekliyor — iş akışını duraksatılmış duruma getir
        return "generate_output"
    
    if review_status == "rejected":
        # Reddedildi — yeniden analiz gerekiyor
        return "prepare_crew_tasks"
    
    # approved veya modified — çıktıya geç
    return "generate_output"


# Node Tanımları Sözlüğü
WORKFLOW_NODES = {
    "analyze_intent": analyze_intent_node,
    "prepare_crew_tasks": prepare_crew_tasks_node,
    "execute_crew_tasks": execute_crew_tasks_node,
    "process_analysis": process_analysis_results_node,
    "generate_output": generate_final_output_node,
    "error_handling": error_handling_node,
    # Yeni node'lar
    "search_information": search_information_node,
    "human_review": human_review_node,
}

# Rota belirleme fonksiyonları
ROUTE_FUNCTIONS = {
    "route_by_intent": route_by_intent,
    "route_after_analysis": route_after_analysis,
    "route_after_review": route_after_review,
}
