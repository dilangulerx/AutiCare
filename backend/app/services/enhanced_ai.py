"""
AutiCare Enhanced AI Services
LangGraph + CrewAI ile çalışan geliştirilmiş AI servisleri
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.crew_manager import get_crew_manager
from app.monitoring import get_monitor
from app.workflow import get_workflow_executor

logger = logging.getLogger(__name__)


class EnhancedAIService:
    """
    Geliştirilmiş AI Servisi
    Mevcut hizmetlerle uyumlu, geliştirilmiş özellikler sunar
    """
    
    def __init__(self):
        """Başlat"""
        self.crew_manager = get_crew_manager()
        self.monitor = get_monitor()
        self.workflow_executor = get_workflow_executor()
        logger.info("✓ EnhancedAIService hazır")
    
    async def analyze_child_behavior(
        self,
        child_name: str,
        logs_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Çocuğun Davranışını Analiz Et
        
        Args:
            child_name: Çocuk adı
            logs_data: Günlük davranış verileri
        
        Returns:
            Analiz sonuçları
        """
        logger.info(f"📊 Davranış Analizi: {child_name}")
        
        logs_text = self._format_logs(logs_data)
        
        result = await self.crew_manager.execute_crew(
            crew_type="analysis",
            child_name=child_name,
            logs_text=logs_text,
        )
        
        if result.get("success"):
            self.monitor.log_crew_execution(
                crew_type="analysis",
                child_name=child_name,
                tasks_executed=1,
            )
        
        return result
    
    async def detect_behavioral_anomalies(
        self,
        child_name: str,
        logs_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Davranışsal Anormallikeri Tespit Et
        
        Args:
            child_name: Çocuk adı
            logs_data: Günlük davranış verileri
        
        Returns:
            Anomali tespiti sonuçları
        """
        logger.info(f"🔍 Anomali Tespiti: {child_name}")
        
        logs_text = self._format_logs(logs_data)
        
        result = await self.crew_manager.execute_crew(
            crew_type="anomaly",
            child_name=child_name,
            logs_text=logs_text,
        )
        
        return result
    
    async def generate_therapy_recommendations(
        self,
        child_name: str,
        logs_data: List[Dict[str, Any]],
        analysis_results: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Terapi Önerileri Oluştur
        
        Args:
            child_name: Çocuk adı
            logs_data: Günlük davranış verileri
            analysis_results: İsteğe bağlı analiz sonuçları
        
        Returns:
            Terapi önerileri
        """
        logger.info(f"💡 Terapi Önerileri: {child_name}")
        
        logs_text = self._format_logs(logs_data)
        
        result = await self.crew_manager.execute_crew(
            crew_type="recommendations",
            child_name=child_name,
            logs_text=logs_text,
        )
        
        return result
    
    async def generate_weekly_report(
        self,
        child_name: str,
        child_id: int,
        parent_id: int,
        logs_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Haftalık Rapor Oluştur
        
        Args:
            child_name: Çocuk adı
            child_id: Çocuk ID'si
            parent_id: Ebeveyn ID'si
            logs_data: Haftalık davranış verileri
        
        Returns:
            Haftalık rapor
        """
        logger.info(f"📋 Haftalık Rapor Oluşturuluyor: {child_name}")
        
        result = await self.workflow_executor.execute(
            child_id=child_id,
            child_name=child_name,
            parent_id=parent_id,
            task_type="report",
            logs_data=logs_data,
            streaming=False,
        )
        
        return result
    
    async def chat_with_parent(
        self,
        child_name: str,
        child_id: int,
        parent_id: int,
        query: str,
        logs_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Ebeveyn ile Sohbet
        
        Args:
            child_name: Çocuk adı
            child_id: Çocuk ID'si
            parent_id: Ebeveyn ID'si
            query: Ebeveynin sorusu
            logs_data: Davranış verileri
        
        Returns:
            Sohbet yanıtı
        """
        logger.info(f"💬 Sohbet: {child_name} - {query[:50]}")
        
        result = await self.workflow_executor.execute(
            child_id=child_id,
            child_name=child_name,
            parent_id=parent_id,
            task_type="chat",
            logs_data=logs_data,
            query=query,
            streaming=False,
        )
        
        return result
    
    async def deep_analysis(
        self,
        child_name: str,
        child_id: int,
        parent_id: int,
        logs_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Derinlemesine Davranış Analizi
        
        Args:
            child_name: Çocuk adı
            child_id: Çocuk ID'si
            parent_id: Ebeveyn ID'si
            logs_data: Davranış verileri
        
        Returns:
            Derinlemesine analiz sonuçları
        """
        logger.info(f"🧬 Derinlemesine Analiz: {child_name}")
        
        result = await self.workflow_executor.execute(
            child_id=child_id,
            child_name=child_name,
            parent_id=parent_id,
            task_type="analysis",
            logs_data=logs_data,
            streaming=False,
        )
        
        return result
    
    @staticmethod
    def _format_logs(logs_data: List[Dict[str, Any]]) -> str:
        """
        Günlükleri metin formatta formatla
        
        Args:
            logs_data: Günlük verileri
        
        Returns:
            Formatlanmış metin
        """
        lines = []
        
        for log in logs_data:
            line = (
                f"[{log.get('date', 'Tarih Yok')}] "
                f"Göz İletişimi: {log.get('eye_contact', 'N/A')}, "
                f"İletişim Puanı: {log.get('communication_score', 'N/A')}, "
                f"Aggresyon: {log.get('aggression_level', 'N/A')}, "
                f"Uyku: {log.get('sleep_hours', 'N/A')}h, "
                f"Notlar: {log.get('notes') or log.get('behavioral_notes', 'Yok')}"
            )
            lines.append(line)
        
        return "\n".join(lines)


# Global instance
_service = None


def get_enhanced_ai_service() -> EnhancedAIService:
    """Global servisi al veya oluştur"""
    global _service
    if _service is None:
        _service = EnhancedAIService()
    return _service
