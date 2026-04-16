"""
AutiCare CrewAI Enhanced Integration
LangGraph ile birlikte çalışan CrewAI entegrasyonu

MODERNIZASYON (v2.0):
- Yeni ajanlar: LiteratureReviewAgent, ParentSupportAgent, DataAnalystAgent
- Araç entegrasyonu: Her ajana uygun araçlar (arama, veritabanı, rapor formatı)
- Yeni crew türleri: deep_analysis, literature_review, parent_support
"""

import logging
import json
import asyncio
from typing import Optional, List, Dict, Any
from crewai import Agent, Task, Crew
import yaml

logger = logging.getLogger(__name__)


class AutiCareCrewManager:
    """
    CrewAI Ekip Yöneticisi
    Davranış analizi, anomali tespiti ve terapi önerisi için ekipler oluşturur
    """
    
    def __init__(self):
        """Ekip Yöneticisini İnit Et"""
        self.agents = {}
        self.crews = {}
        self._load_config()
        logger.info("✓ AutiCareCrewManager başlatıldı")
    
    def _load_config(self):
        """
        Konfigurasyon dosyalarını yükle
        agents.yaml ve tasks.yaml'den
        """
        try:
            from pathlib import Path
            
            # Dosyaların konumunu bulundukları dizinden hesapla
            base_dir = Path(__file__).parent
            agents_file = base_dir / "crew_config" / "agents.yaml"
            tasks_file = base_dir / "crew_config" / "tasks.yaml"
            
            # agents.yaml yükle
            with open(str(agents_file), "r", encoding="utf-8") as f:
                agents_config = yaml.safe_load(f) or []
            
            # tasks.yaml yükle
            with open(str(tasks_file), "r", encoding="utf-8") as f:
                tasks_config = yaml.safe_load(f) or []
            
            logger.info(f"✓ {len(agents_config)} agent konfigürasyonu yüklendi")
            logger.info(f"✓ {len(tasks_config)} görev konfigürasyonu yüklendi")
            
            self.agents_config = {a["agent_name"]: a for a in agents_config}
            self.tasks_config = {t["task_name"]: t for t in tasks_config}
        
        except Exception as e:
            logger.warning(f"⚠️ Konfigurasyon yüklenemedi: {e}")
            self.agents_config = {}
            self.tasks_config = {}
    
    def create_crew(
        self,
        crew_type: str,
        child_name: str,
        logs_text: str,
        query: Optional[str] = None,
    ) -> Optional[Crew]:
        """
        Belirli bir amaç için CrewAI ekibi oluştur
        
        Args:
            crew_type: Ekip türü ("analysis", "anomaly", "recommendations", "report", "chat")
            child_name: Çocuğun adı
            logs_text: Davranış günlüğü metni
            query: Sohbet sorusu (chat ekibi için)
        
        Returns:
            Crew: CrewAI ekibi veya None
        """
        
        agents_list = []
        tasks_list = []
        
        # Crew türüne göre ajanları ve görevleri seç
        if crew_type == "analysis":
            agents_list = self._select_agents(["BehavioralAnalystAgent"])
            tasks_list = self._create_tasks(
                agents_list,
                ["analyze_logs_task"],
                child_name,
                logs_text,
            )
        
        elif crew_type == "anomaly":
            agents_list = self._select_agents(["AnomalyDetectorAgent"])
            tasks_list = self._create_tasks(
                agents_list,
                ["detect_anomalies_task"],
                child_name,
                logs_text,
            )
        
        elif crew_type == "recommendations":
            agents_list = self._select_agents(["TherapyAdvisorAgent"])
            tasks_list = self._create_tasks(
                agents_list,
                ["generate_recommendations_task"],
                child_name,
                logs_text,
            )
        
        elif crew_type == "report":
            agents_list = self._select_agents([
                "BehavioralAnalystAgent",
                "AnomalyDetectorAgent",
                "TherapyAdvisorAgent",
                "ReportGeneratorAgent",
            ])
            tasks_list = self._create_tasks(
                agents_list,
                [
                    "analyze_logs_task",
                    "detect_anomalies_task",
                    "generate_recommendations_task",
                    "compile_weekly_report_task",
                ],
                child_name,
                logs_text,
            )
        
        elif crew_type == "chat":
            agents_list = self._select_agents(["ConversationalAgent"])
            tasks_list = self._create_tasks(
                agents_list,
                ["handle_chat_query_task"],
                child_name,
                logs_text,
                query,
            )
        
        # ── YENİ CREW TÜRLERİ ──
        
        # NEDEN: Mevcut analiz yüzeyseldi. deep_analysis, DataAnalystAgent'ı
        # kullanarak korelasyonları ve zaman serisi trendlerini analiz eder.
        elif crew_type == "deep_analysis":
            agents_list = self._select_agents([
                "BehavioralAnalystAgent",
                "DataAnalystAgent",
                "AnomalyDetectorAgent",
                "TherapyAdvisorAgent",
            ])
            tasks_list = self._create_tasks(
                agents_list,
                [
                    "analyze_logs_task",
                    "deep_data_analysis_task",
                    "detect_anomalies_task",
                    "search_enhanced_recommendations_task",
                ],
                child_name,
                logs_text,
            )
        
        # NEDEN: Terapi önerilerinin bilimsel dayanaklarla desteklenmesi
        # güvenilirliği artırır. LiteratureReviewAgent güncel kaynakları tarar.
        elif crew_type == "literature_review":
            agents_list = self._select_agents([
                "LiteratureReviewAgent",
                "TherapyAdvisorAgent",
            ])
            tasks_list = self._create_tasks(
                agents_list,
                [
                    "literature_review_task",
                    "search_enhanced_recommendations_task",
                ],
                child_name,
                logs_text,
            )
        
        # NEDEN: Ebeveynler sadece veri istemez, pratik destek ve
        # rehberlik de ister. ParentSupportAgent bunu sağlar.
        elif crew_type == "parent_support":
            agents_list = self._select_agents([
                "ParentSupportAgent",
                "ConversationalAgent",
            ])
            tasks_list = self._create_tasks(
                agents_list,
                [
                    "parent_guidance_task",
                    "handle_chat_query_task",
                ],
                child_name,
                logs_text,
                query,
            )
        
        if not agents_list or not tasks_list:
            logger.warning(f"⚠️ Ekip oluşturulamadı: {crew_type}")
            return None
        
        # Crew'ı oluştur
        crew = Crew(
            agents=agents_list,
            tasks=tasks_list,
            verbose=True,
            memory=True,
        )
        
        logger.info(f"✓ Crew oluşturuldu: {crew_type} ({len(agents_list)} ajan, {len(tasks_list)} görev)")
        
        return crew
    
    def _select_agents(self, agent_names: List[str]) -> List[Agent]:
        """
        Yapılandırmadan ajanları seç ve uygun araçları bağla.
        
        NEDEN ARAÇ BAĞLAMA?
        Mevcut ajanlar araç kullanamıyordu. Artık her ajan türüne göre
        uygun araçlar (arama, veritabanı, rapor) otomatik bağlanır.
        
        Args:
            agent_names: Ajan adlarının listesi
        
        Returns:
            Agent listesi
        """
        agents = []
        
        for agent_name in agent_names:
            agent_config = self.agents_config.get(agent_name)
            if not agent_config:
                logger.warning(f"⚠️ Ajan bulunamadı: {agent_name}")
                continue
            
            try:
                # Ajana uygun araçları al
                from app.tools import get_tools_for_agent
                agent_tools = get_tools_for_agent(agent_name)
                
                agent = Agent(
                    role=agent_config.get("role", ""),
                    goal=agent_config.get("goal", ""),
                    backstory=agent_config.get("backstory", ""),
                    verbose=agent_config.get("verbose", False),
                    allow_delegation=agent_config.get("allow_delegation", False),
                    tools=agent_tools if agent_tools else [],
                )
                agents.append(agent)
                tools_info = f" (araçlar: {len(agent_tools)})" if agent_tools else ""
                logger.debug(f"  ✓ {agent_name} eklendi{tools_info}")
            
            except Exception as e:
                logger.error(f"❌ {agent_name} oluşturulamadı: {e}")
        
        return agents
    
    def _create_tasks(
        self,
        agents: List[Agent],
        task_names: List[str],
        child_name: str,
        logs_text: str,
        query: Optional[str] = None,
    ) -> List[Task]:
        """
        Görevleri oluştur
        
        Args:
            agents: Ajan listesi
            task_names: Görev adlarının listesi
            child_name: Çocuk adı
            logs_text: Davranış verileri
            query: İsteğe bağlı sohbet sorgusu
        
        Returns:
            Task listesi
        """
        tasks = []
        agent_idx = 0
        
        for task_name in task_names:
            task_config = self.tasks_config.get(task_name)
            if not task_config:
                logger.warning(f"⚠️ Görev konfigürasyonu bulunamadı: {task_name}")
                continue
            
            # Açıklamayı format et
            description = task_config.get("description", "").format(
                child_name=child_name,
                logs_text=logs_text,
                query=query or "",
            )
            
            try:
                # Görev için ajan seç
                if agent_idx < len(agents):
                    agent = agents[agent_idx]
                    agent_idx += 1
                else:
                    agent = agents[0] if agents else None
                
                if not agent:
                    continue
                
                task = Task(
                    description=description,
                    expected_output=task_config.get("expected_output", ""),
                    agent=agent,
                )
                tasks.append(task)
                logger.debug(f"  ✓ {task_name} eklendi")
            
            except Exception as e:
                logger.error(f"❌ {task_name} oluşturulamadı: {e}")
        
        return tasks
    
    async def execute_crew(
        self,
        crew_type: str,
        child_name: str,
        logs_text: str,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        CrewAI Ekipini Çalıştır
        
        Args:
            crew_type: Ekip türü
            child_name: Çocuk adı
            logs_text: Davranış verileri
            query: İsteğe bağlı sohbet sorgusu
        
        Returns:
            Ekibin çalıştırma sonuçları
        """
        
        logger.info(f"🤖 Crew Çalıştırılıyor: {crew_type}")
        
        crew = self.create_crew(crew_type, child_name, logs_text, query)
        if not crew:
            return {
                "success": False,
                "error": f"Crew oluşturulamadı: {crew_type}",
            }
        
        try:
            # Crew'ı çalıştır — kickoff() senkron, event loop'u bloklamemak için to_thread kullan
            result = await asyncio.to_thread(crew.kickoff)
            
            logger.info(f"✓ Crew Çalıştırması Tamamlandı")
            
            return {
                "success": True,
                "crew_type": crew_type,
                "output": str(result),
                "tasks_executed": len(crew.tasks),
                "agents_used": len(crew.agents),
            }
        
        except Exception as e:
            logger.error(f"❌ Crew Çalıştırması Başarısız: {e}", exc_info=True)
            
            return {
                "success": False,
                "crew_type": crew_type,
                "error": str(e),
            }
    
    def get_crew_info(self) -> Dict[str, Any]:
        """Crew Yöneticisi bilgilerini al"""
        return {
            "manager": "AutiCareCrewManager",
            "version": "2.0.0",
            "agents_loaded": len(self.agents_config),
            "tasks_loaded": len(self.tasks_config),
            "crew_types": [
                "analysis", "anomaly", "recommendations", "report", "chat",
                "deep_analysis", "literature_review", "parent_support",
            ],
            "agents": list(self.agents_config.keys()),
            "features": [
                "tool_integration",
                "search_capability",
                "database_query",
                "report_formatting",
            ],
        }


# Global Crew Manager instance'ı
_crew_manager = None


def get_crew_manager() -> AutiCareCrewManager:
    """Global Crew Manager'ı al veya oluştur"""
    global _crew_manager
    if _crew_manager is None:
        _crew_manager = AutiCareCrewManager()
    return _crew_manager
