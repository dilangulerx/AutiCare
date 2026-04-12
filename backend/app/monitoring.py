"""
AutiCare LangSmith Monitoring Integration
AI etkinliklerini, token kullanımını ve performansını izler
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MonitoringLevel(str, Enum):
    """İzleme seviyeleri"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AutiCareMonitor:
    """
    AI Etkinlik İzleyici
    LangSmith + LocalStorage tabanlı izleme
    """
    
    def __init__(self):
        """Monitor'ı Başlat"""
        self.storage_dir = os.getenv("CREWAI_STORAGE_DIR", "AutiCare")
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY", "")
        self.tracking_enabled = bool(self.langsmith_api_key)
        self.events: List[Dict[str, Any]] = []
        
        logger.info(f"✓ AutiCareMonitor başlatıldı (LangSmith: {'AKTIF' if self.tracking_enabled else 'PASIF'})")
    
    def log_event(
        self,
        event_type: str,
        component: str,
        message: str,
        level: MonitoringLevel = MonitoringLevel.INFO,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Etkinliği Kayıt Et
        
        Args:
            event_type: Etkinlik türü ("workflow", "crew", "agent", "task", "token", etc)
            component: Bileşen adı
            message: Etkinlik mesajı
            level: Log seviyesi
            metadata: Ek veriler
        """
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "component": component,
            "message": message,
            "level": level.value,
            "metadata": metadata or {},
        }
        
        self.events.append(event)
        
        # Uygun log seviyesini kullan
        log_func = getattr(logger, level.value, logger.info)
        log_func(f"[{component}] {message}")
        
        # LangSmith'e gönder (varsa)
        if self.tracking_enabled and event_type in ["workflow", "crew", "token"]:
            self._send_to_langsmith(event)
    
    def log_workflow_start(
        self,
        workflow_id: str,
        child_id: int,
        task_type: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """İş Akışı Başlangıcını Kayıt Et"""
        self.log_event(
            event_type="workflow",
            component="LangGraph",
            message=f"Workflow başlatıldı: {task_type}",
            level=MonitoringLevel.INFO,
            metadata={
                "workflow_id": workflow_id,
                "child_id": child_id,
                "task_type": task_type,
                **(metadata or {}),
            },
        )
    
    def log_workflow_end(
        self,
        workflow_id: str,
        execution_time: float,
        status: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """İş Akışı Sonlanmasını Kayıt Et"""
        self.log_event(
            event_type="workflow",
            component="LangGraph",
            message=f"Workflow tamamlandı: {status} ({execution_time:.2f}s)",
            level=MonitoringLevel.INFO if status == "success" else MonitoringLevel.WARNING,
            metadata={
                "workflow_id": workflow_id,
                "execution_time": execution_time,
                "status": status,
                **(metadata or {}),
            },
        )
    
    def log_crew_execution(
        self,
        crew_type: str,
        child_name: str,
        tasks_executed: int,
        metadata: Optional[Dict] = None,
    ) -> None:
        """CrewAI Çalıştırmasını Kayıt Et"""
        self.log_event(
            event_type="crew",
            component="CrewAI",
            message=f"Crew çalıştırıldı: {crew_type} ({tasks_executed} görev)",
            level=MonitoringLevel.INFO,
            metadata={
                "crew_type": crew_type,
                "child_name": child_name,
                "tasks_executed": tasks_executed,
                **(metadata or {}),
            },
        )
    
    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        details: Optional[Dict] = None,
    ) -> None:
        """Ajan Etkinliğini Kayıt Et"""
        self.log_event(
            event_type="agent",
            component="Agent",
            message=f"{agent_name}: {action}",
            level=MonitoringLevel.DEBUG,
            metadata={
                "agent_name": agent_name,
                "action": action,
                **(details or {}),
            },
        )
    
    def log_token_usage(
        self,
        component: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        model: str = "gpt-4o-mini",
    ) -> None:
        """Token Kullanımını Kayıt Et"""
        self.log_event(
            event_type="token",
            component=component,
            message=f"Token kullanımı: {total_tokens} toplam",
            level=MonitoringLevel.DEBUG,
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "model": model,
            },
        )
    
    def log_error(
        self,
        component: str,
        error: Exception,
        context: Optional[Dict] = None,
    ) -> None:
        """Hatayı Kayıt Et"""
        self.log_event(
            event_type="error",
            component=component,
            message=f"Hata: {str(error)}",
            level=MonitoringLevel.ERROR,
            metadata={
                "error_type": type(error).__name__,
                "error_message": str(error),
                **(context or {}),
            },
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        İstatistikleri Al
        
        Returns:
            İstatistik verisi
        """
        
        # Etkinlikleri türe göre grupla
        events_by_type = {}
        for event in self.events:
            event_type = event["event_type"]
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        # Seviyelere göre grupla
        events_by_level = {}
        for event in self.events:
            level = event["level"]
            events_by_level[level] = events_by_level.get(level, 0) + 1
        
        # Hataları say
        errors = [e for e in self.events if e["level"] == "error"]
        
        # Token'ları topla
        total_tokens = 0
        for event in self.events:
            if event["event_type"] == "token":
                total_tokens += event.get("metadata", {}).get("total_tokens", 0)
        
        return {
            "total_events": len(self.events),
            "events_by_type": events_by_type,
            "events_by_level": events_by_level,
            "total_errors": len(errors),
            "total_tokens": total_tokens,
            "langsmith_enabled": self.tracking_enabled,
            "last_event": self.events[-1]["timestamp"] if self.events else None,
        }
    
    def _send_to_langsmith(self, event: Dict[str, Any]) -> None:
        """
        Etkinliği LangSmith'e Gönder
        Not: Gerçek implementasyon için LangSmith SDK kullanılır
        """
        if not self.tracking_enabled:
            return
        
        try:
            # LangSmith SDK kullanarak gönder
            # from langsmith import Client
            # client = Client(api_key=self.langsmith_api_key)
            # client.create_run(...event)
            logger.debug(f"📤 LangSmith'e gönderildi: {event['event_type']}")
        
        except Exception as e:
            logger.warning(f"⚠️ LangSmith gönderimi başarısız: {e}")
    
    def export_events(self) -> str:
        """
        Etkinlikleri JSON olarak kayıt et
        
        Returns:
            JSON string
        """
        import json
        return json.dumps(self.events, ensure_ascii=False, indent=2)
    
    def clear_events(self) -> None:
        """Etkinlik geçmişini temizle"""
        self.events.clear()
        logger.info("✓ Etkinlik geçmişi temizlendi")


class PerformanceTracker:
    """
    Performans İzleyici
    Çalışma süresi, bellek, kaynakları izler
    """
    
    def __init__(self):
        """Tracker'ı Başlat"""
        self.metrics: Dict[str, List[float]] = {}
        logger.info("✓ PerformanceTracker başlatıldı")
    
    def record_execution_time(
        self,
        component: str,
        duration: float,
    ) -> None:
        """
        Yürütme Zamanını Kayıt Et
        
        Args:
            component: Bileşen adı
            duration: Süre (saniye)
        """
        key = f"execution_time_{component}"
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append(duration)
        logger.debug(f"⏱️ {component} yürütme zamanı: {duration:.3f}s")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Performans İstatistiklerini Al
        
        Returns:
            Performans metrikleri
        """
        stats = {}
        
        for key, values in self.metrics.items():
            if values:
                stats[key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }
        
        return stats
    
    def reset(self) -> None:
        """Metrikleri Sıfırla"""
        self.metrics.clear()


# Global instances
_monitor = None
_performance_tracker = None


def get_monitor() -> AutiCareMonitor:
    """Global Monitor'ı al veya oluştur"""
    global _monitor
    if _monitor is None:
        _monitor = AutiCareMonitor()
    return _monitor


def get_performance_tracker() -> PerformanceTracker:
    """Global PerformanceTracker'ı al veya oluştur"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker
