"""
AutiCare Hibrit AI Sistemi - Entegrasyon Testi
LangGraph + CrewAI kurulumunu test et
"""

import asyncio
import sys
from pathlib import Path

# Backend'i path'a ekle
sys.path.insert(0, str(Path(__file__).parent / "backend"))


async def test_workflow_initialization():
    """LangGraph Workflow'unu Test Et"""
    print("\n" + "="*60)
    print("🧪 TEST 1: LangGraph Workflow İnitiyalizasyonu")
    print("="*60)
    
    try:
        from app.workflow import get_workflow_executor
        
        executor = get_workflow_executor()
        info = executor.get_workflow_info()
        
        print(f"✓ Workflow başarıyla yüklendi")
        print(f"  - Ad: {info['name']}")
        print(f"  - Node'lar: {len(info['nodes'])} adet")
        print(f"  - Desteklenen Görevler: {info['supported_tasks']}")
        
        return True
    
    except Exception as e:
        print(f"✗ Workflow başarısız: {e}")
        return False


async def test_crew_manager_initialization():
    """CrewAI Crew Manager'ını Test Et"""
    print("\n" + "="*60)
    print("🧪 TEST 2: CrewAI Crew Manager İnitiyalizasyonu")
    print("="*60)
    
    try:
        from app.crew_manager import get_crew_manager
        
        manager = get_crew_manager()
        info = manager.get_crew_info()
        
        print(f"✓ CrewAI başarıyla yüklendi")
        print(f"  - Ajan Sayısı: {info['agents_loaded']}")
        print(f"  - Görev Sayısı: {info['tasks_loaded']}")
        print(f"  - Desteklenen Crew Türleri: {info['crew_types']}")
        
        if info['agents_loaded'] > 0:
            print(f"  - Ajanlar: {', '.join(info['agents'][0:3])}...")
        
        return True
    
    except Exception as e:
        print(f"✗ CrewAI başarısız: {e}")
        return False


async def test_monitoring_system():
    """İzleme Sistemi'ni Test Et"""
    print("\n" + "="*60)
    print("🧪 TEST 3: Monitoring Sistemi")
    print("="*60)
    
    try:
        from app.monitoring import get_monitor, get_performance_tracker
        
        monitor = get_monitor()
        perf = get_performance_tracker()
        
        # Test etkinliği kayıt et
        monitor.log_event(
            event_type="test",
            component="TestRunner",
            message="Test mesajı",
        )
        
        # İstatistikleri al
        stats = monitor.get_statistics()
        
        print(f"✓ Monitoring başarıyla yüklendi")
        print(f"  - Kayıt Edilen Etkinlikler: {stats['total_events']}")
        print(f"  - LangSmith Etkin: {stats['langsmith_enabled']}")
        print(f"  - Hata Sayısı: {stats['total_errors']}")
        
        return True
    
    except Exception as e:
        print(f"✗ Monitoring başarısız: {e}")
        return False


async def test_state_initialization():
    """State Yönetimi'ni Test Et"""
    print("\n" + "="*60)
    print("🧪 TEST 4: State Yönetimi")
    print("="*60)
    
    try:
        from app.state import init_state, SUPPORTED_TASKS
        
        # Test durumu oluştur
        state = init_state(
            child_id=1,
            child_name="TestÇocuğu",
            parent_id=1,
            task_type="report",
            logs_data=[]
        )
        
        print(f"✓ State başarıyla oluşturuldu")
        print(f"  - Görev Türü: {state['current_task']}")
        print(f"  - Durumu: {state['task_status']}")
        print(f"  - Desteklenen Görevler: {len(SUPPORTED_TASKS)}")
        
        return True
    
    except Exception as e:
        print(f"✗ State başarısız: {e}")
        return False


async def test_package_imports():
    """Tüm Paket İthalatlarını Test Et"""
    print("\n" + "="*60)
    print("🧪 TEST 5: Paket İthalatları")
    print("="*60)
    
    packages = [
        ("langgraph", "LangGraph"),
        ("langchain", "LangChain"),
        ("langchain_openai", "LangChain OpenAI"),
        ("langsmith", "LangSmith"),
        ("crewai", "CrewAI"),
        ("pydantic", "Pydantic"),
        ("fastapi", "FastAPI"),
    ]
    
    failed = []
    
    for module_name, display_name in packages:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name}")
        except ImportError:
            print(f"  ✗ {display_name} (EKSIK)")
            failed.append(display_name)
    
    if failed:
        print(f"\n  ⚠️  {len(failed)} paket eksik:")
        for pkg in failed:
            print(f"    - {pkg}")
        return False
    
    print(f"\n✓ Tüm paketler başarıyla yüklendi!")
    return True


async def run_all_tests():
    """Tüm Testleri Çalıştır"""
    print("\n")
    print("🚀 AutiCare Hibrit AI Sistemi - Entegrasyon Testi")
    print("╔" + "="*58 + "╗")
    print("║     LangGraph + CrewAI + LangSmith Kurulum Doğrulama     ║")
    print("╚" + "="*58 + "╝")
    
    results = {
        "Paket İthalatları": await test_package_imports(),
        "State Yönetimi": await test_state_initialization(),
        "Monitoring Sistemi": await test_monitoring_system(),
        "LangGraph Workflow": await test_workflow_initialization(),
        "CrewAI Crew Manager": await test_crew_manager_initialization(),
    }
    
    # Özet
    print("\n" + "="*60)
    print("📊 TEST ÖZETI")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ GEÇTI" if result else "✗ BAŞARISIZ"
        print(f"{status}: {test_name}")
    
    print(f"\nSonuç: {passed}/{total} test geçildi")
    
    if passed == total:
        print("\n🎉 TÜM TESTLER BAŞARILI! Sistem hazır.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test başarısız oldu.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
