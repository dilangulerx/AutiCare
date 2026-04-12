# ⚡ AutiCare Hibrit AI - Quick Start Rehberi

## 🎯 5 Dakikada Başlayın

### Adım 1: Bağımlılıkları Kur (2 dakika)

```bash
cd backend
pip install -r requirements.txt
```

✅ Yüklü olacak paketler:
- langgraph, langsmith, langchain
- crewai, pydantic, fastapi
- Tüm AI ve veritabanı paketleri

### Adım 2: Ortam Ayarlarını Yapılandır (1 dakika)

`.env` dosyanızın şu değişkenleri içerdiğinden emin olun:

```env
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/autism_tracker

# İsteğe Bağlı (LangSmith Monitoring)
# LANGSMITH_API_KEY=ls_your_key_here
```

### Adım 3: Backend'i Çalıştır (1 dakika)

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Expected Output:
```
✓ AutiCare Workflow Executor başlatıldı
✓ AutiCareCrewManager başlatıldı
✓ LangGraph Workflow: AutiCare Hibrit AI İş Akışı
✓ CrewAI: 5 ajan, 5 görev yüklü
✓ AutiCare API Hazır!
```

### Adım 4: Frontend'i Çalıştır (Opsiyonel - 1 dakika)

Başka bir terminal'de:
```bash
cd frontend
npm install
npm run dev
```

### Adım 5: Sistem Sağlığını Kontrol Et (1 dakika)

```bash
# Terminal'de
curl http://localhost:8000/health

# Yanıt:
# {"status":"ok","version":"2.0.0"}
```

---

## 🧪 İlk Test

### API Test'ini Çalıştır

```bash
cd backend

# Entegrasyon testini çalıştır
python test_integration.py
```

Expected Output:
```
🚀 AutiCare Hibrit AI Sistemi - Entegrasyon Testi
════════════════════════════════════════════════════════

✓ GEÇTI: Paket İthalatları
✓ GEÇTI: State Yönetimi
✓ GEÇTI: Monitoring Sistemi
✓ GEÇTI: LangGraph Workflow
✓ GEÇTI: CrewAI Crew Manager

Sonuç: 5/5 test geçildi

🎉 TÜM TESTLER BAŞARILI! Sistem hazır.
```

---

## 🔌 API Endpoint'lerini Test Et

### 1️⃣ Sistem Bilgisi

```bash
curl http://localhost:8000/ai/v2/workflow/info | jq
```

### 2️⃣ Haftalık Rapor Oluştur

```bash
curl -X POST http://localhost:8000/ai/v2/workflow/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_type": "report",
    "streaming": false
  }'
```

### 3️⃣ Sohbet (Geliştirilmiş)

```bash
curl -X POST http://localhost:8000/ai/v2/workflow/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_type": "chat",
    "query": "Ahmet bu hafta nasıl geçti?",
    "streaming": false
  }'
```

### 4️⃣ Anomali Tespiti

```bash
curl -X POST http://localhost:8000/ai/v2/workflow/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_type": "anomaly",
    "streaming": false
  }'
```

### 5️⃣ Monitoring İstatistikleri

```bash
curl http://localhost:8000/ai/v2/monitoring/stats | jq
```

---

## 🐍 Python Kodda Kullanım

```python
import asyncio
from app.workflow import get_workflow_executor
from app.monitoring import get_monitor

async def main():
    # Executor'ı al
    executor = get_workflow_executor()
    
    # Haftalık rapor oluştur
    result = await executor.execute(
        child_id=1,
        child_name="Ahmet",
        parent_id=1,
        task_type="report",
        logs_data=[
            {
                "date": "2024-03-01",
                "eye_contact": 7,
                "communication_score": 8,
                "aggression_level": 2,
                "sleep_hours": 8
            }
        ]
    )
    
    if result['success']:
        print(f"✓ Rapor oluşturuldu!")
        print(f"  Output: {result['output'][:100]}...")
        print(f"  Süre: {result['execution_time']:.2f}s")
        print(f"  Anomaliler: {len(result['anomalies']) if result['anomalies'] else 0}")
    
    # İstatistikleri göster
    monitor = get_monitor()
    stats = monitor.get_statistics()
    print(f"\nMonitoring Stats:")
    print(f"  Toplam Etkinlikler: {stats['total_events']}")
    print(f"  Toplam Token: {stats['total_tokens']}")

# Çalıştır
asyncio.run(main())
```

---

## 🐳 Docker ile Başlat

### Option 1: Tek Komut

```bash
cd /Users/dilanguler/Desktop/autism-tracker
docker-compose up --build
```

### Option 2: Manuel

```bash
# Terminal 1: MySQL
docker run -d \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=autism_tracker \
  -p 3307:3306 \
  --name autism_db \
  mysql:8.0

# Terminal 2: Backend
cd backend
docker build -t autism-backend .
docker run -p 8000:8000 \
  -e DATABASE_URL="mysql+pymysql://..." \
  -e OPENAI_API_KEY="sk-..." \
  autism-backend
```

---

## 📊 Önemli Komutlar

```bash
# 1. Testleri Çalıştır
cd backend
python test_integration.py

# 2. Log Dosyasını Kontrol Et
tail -f logs/app.log

# 3. Database'i Sıfırla
python -c "from app.database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"

# 4. CrewAI Storage'ı Temizle
rm -rf AutiCare/

# 5. Tüm BreakPoint'leri Kaldır (Debug)
grep -r "breakpoint()" app/ || echo "No breakpoints found"
```

---

## 🔍 Hata Çözümü

### Problem: "langgraph not found"
```bash
pip install langgraph==0.2.15
```

### Problem: "No module named 'crewai'"
```bash
pip install crewai==1.11.1
```

### Problem: "Database connection failed"
- `.env`'de DATABASE_URL kontrol et
- MySQL servisinin çalışıp çalışmadığını kontrol et

### Problem: "OpenAI API error"
- `.env`'de OPENAI_API_KEY kontrol et
- API key'in geçerliliğini kontrol et

### Problem: "Agents not loaded"
```bash
# agents.yaml dosyasını kontrol et
cat backend/app/crew_config/agents.yaml
```

---

## 📈 Performans Tipleri

### Tipik Yanıt Süreleri

```
Görev Türü          Beklenen Süre    Factors
────────────────────────────────────────────────
report              15-30 saniye     • Model seçimi
chat                5-10 saniye      • Query uzunluğu
anomaly             8-15 saniye      • Log sayısı
analysis            20-40 saniye     • Veri miktarı

Örneğin:
• gpt-4o-mini:    ~10-15 saniye (varsayılan)
• gpt-4-turbo:    ~5-10 saniye
• gpt-3.5-turbo:  ~3-5 saniye
```

---

## 🎓 Katmanlar & Yapı

```
Frontend (React/TypeScript)
    ↓ /ai/v2/workflow/{child_id}
FastAPI Router (app/routers/ai.py)
    ↓ executeWorkflow()
LangGraph Executor (app/workflow.py)
    ↓ state flow
Workflow Nodes (app/workflow_nodes.py)
    ├ analyze_intent
    ├ prepare_crew_tasks
    ├ execute_crew_tasks
    ├ process_analysis
    └ generate_output
    ↓
CrewAI Crew Manager (app/crew_manager.py)
    ├ BehavioralAnalystAgent
    ├ AnomalyDetectorAgent
    ├ TherapyAdvisorAgent
    ├ ReportGeneratorAgent
    └ ConversationalAgent
    ↓
OpenAI API (GPT-4o mini)
    ↓ response
Monitoring System (app/monitoring.py)
    ├ Event logging
    ├ Token tracking
    └ LangSmith (optional)
    ↓
Database (MySQL)
```

---

## 📚 Sonraki Adımlar

1. ✅ Backend'i kurup test et
2. ✅ Endpoint'leri test et (curl/Postman)
3. ✅ Frontend bağlantısını kontrol et
4. ✅ Monitoring istatistiklerini gözlemle
5. ⏳ Custom workflow node'ları ekle (optional)
6. ⏳ Streaming desteği ekle (optional)
7. ⏳ Caching layer ekle (optional)

---

## 💬 Sorular?

- 📖 Rehber: `SETUP_LANGGRAPH_CREWAI.md`
- 📊 Özet: `IMPLEMENTATION_SUMMARY.md`
- 🧪 Test: `python backend/test_integration.py`
- 🔗 Docs: https://docs.langchain.com/langgraph

---

**Başarılar! 🎉**
