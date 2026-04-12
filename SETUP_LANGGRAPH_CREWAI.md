# AutiCare LangGraph + CrewAI Hibrit AI Kurulum Rehberi

## 🎯 Genel Bakış

AutiCare 2.0, LangGraph orchestration sistemi ile CrewAI agent yönetimini birleştiren hibrit bir AI mimarisidir.

### Mimarinin Bileşenleri

1. **LangGraph (Orchestration)**: İş akışınızı, durumunu ve veri akışını yönetir
2. **CrewAI (Execution)**: Belirli görevleri çalıştıran otonom ajanları yönetir
3. **LangSmith (Monitoring)**: Tüm AI etkinliklerini izler ve loglar

```
┌─────────────────────────────────────────────┐
│   FastAPI Endpoint (ai.py)                   │
├─────────────────────────────────────────────┤
│   LangGraph Workflow (workflow.py)           │
│   ├─ State Management (state.py)             │
│   └─ Workflow Nodes (workflow_nodes.py)      │
├─────────────────────────────────────────────┤
│   CrewAI Crew Manager (crew_manager.py)      │
│   └─ Agents + Tasks                          │
├─────────────────────────────────────────────┤
│   Monitoring System (monitoring.py)          │
│   └─ LangSmith Integration                   │
└─────────────────────────────────────────────┘
```

## 📦 Yükleme Adımları

### 1. Bağımlılıkları Kur

```bash
cd backend
pip install -r requirements.txt
```

**Yeni Paketler:**
- `langgraph==0.2.15` - Workflow orchestration
- `langsmith==0.2.14` - Monitoring ve tracing
- `langchain==0.3.1` - LLM utilities
- `langchain-openai==0.2.0` - OpenAI integration
- `langchain-core==0.3.5` - Core LangChain

### 2. Ortam Değişkenlerini Ayarla

`.env` dosyasında:

```env
# Mevcut değişkenler
OPENAI_API_KEY=sk-...
DATABASE_URL=mysql+pymysql://...

# Yeni: LangSmith (İsteğe Bağlı)
LANGSMITH_API_KEY=ls_...      # LangSmith API anahtarı (isteğe bağlı)
LANGSMITH_PROJECT=AutiCare    # Proje adı

# Mevcut: CrewAI Storage
CREWAI_STORAGE_DIR=AutiCare   # Zaten tanımlı
```

### 3. CrewAI Konfigürasyonunu Doğrula

`backend/app/crew_config/` klasöründe:
- `agents.yaml` - Ajanları tanımlar
- `tasks.yaml` - Görevleri tanımlar

Her ikisi de mevcut ve düzgün yapılandırılmış.

### 4. Sunucuyu Başlat

```bash
# Geliştirme modunda
python -m uvicorn app.main:app --reload --port 8000

# Üretim modunda
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🚀 Kullanım

### Klasik Endpoint'ler (Uyumlu)

```bash
# Sohbet
POST /ai/chat/{child_id}
{
  "message": "Ahmet'in bu hafta nasıl geçti?"
}

# Anomali Tespiti
GET /ai/anomaly/{child_id}
```

### Yeni LangGraph Workflow Endpoint'leri

#### 1. Haftalık Rapor Oluştur

```bash
POST /ai/v2/workflow/{child_id}
{
  "task_type": "report",
  "streaming": false
}
```

**Yanıt:**
```json
{
  "success": true,
  "status": "completed",
  "output": "Haftalık rapor...",
  "analysis": { ... },
  "anomalies": [ ... ],
  "recommendations": [ ... ],
  "execution_time": 15.23
}
```

#### 2. Sohbet (Geliştirilmiş)

```bash
POST /ai/v2/workflow/{child_id}
{
  "task_type": "chat",
  "query": "Ahmet'in konuşması nasıl?",
  "streaming": false
}
```

#### 3. Anomali Tespiti (Geliştirilmiş)

```bash
POST /ai/v2/workflow/{child_id}
{
  "task_type": "anomaly",
  "streaming": false
}
```

#### 4. Derinlemesine Analiz

```bash
POST /ai/v2/workflow/{child_id}
{
  "task_type": "analysis",
  "streaming": false
}
```

#### 5. Doğrudan CrewAI Ekibi Çalıştır

```bash
POST /ai/v2/crew/{crew_type}/{child_id}
```

**Crew Types:**
- `analysis` - Davranış Analizi
- `anomaly` - Anomali Tespiti
- `recommendations` - Terapi Önerileri
- `report` - Haftalık Rapor
- `chat` - Sohbet

### İzleme Endpoint'leri

#### A. Workflow Bilgileri

```bash
GET /ai/v2/workflow/info
```

**Yanıt:**
```json
{
  "workflow": {
    "name": "AutiCare Hibrit AI İş Akışı",
    "nodes": ["analyze_intent", "prepare_crew_tasks", ...],
    "supported_tasks": ["report", "chat", "anomaly", "analysis"]
  },
  "crew": {
    "agents_loaded": 5,
    "tasks_loaded": 5,
    "crew_types": ["analysis", "anomaly", ...]
  },
  "monitoring": {
    "statistics": { ... },
    "langsmith_enabled": true
  }
}
```

#### B. İzleme İstatistikleri

```bash
GET /ai/v2/monitoring/stats
```

#### C. Sistem Sağlığı

```bash
GET /ai/health
```

## 📊 İş Akışı Mimarisi

### LangGraph Workflow Akışı

```
START
  ↓
[analyze_intent] → Niyeti analiz et
  ↓
[prepare_crew_tasks] → Çalıştırılacak CrewAI görevlerini hazırla
  ↓
[execute_crew_tasks] → CrewAI'ı çalıştır
  ↓
[process_analysis] → Sonuçları işle ve mesajları güncelle
  ↓
[generate_output] → Son çıktıyı oluştur
  ↓
END

ERROR: Herhangi bir noktada hata → [error_handling] → END
```

### State Yapısı (AutiCareState)

```python
{
  "messages": [],                    # Konuşma geçmişi
  "child_id": 1,                     # Çocuk ID'si
  "child_name": "Ahmet",             # Çocuk adı
  "parent_id": 1,                    # Ebeveyn ID'si
  "logs_data": [...],                # Günlük davranış verileri
  "current_task": "report",          # Mevcut görev
  "task_status": "processing",       # Görev durumu
  "analysis_result": {...},          # Analiz sonuçları
  "anomalies": [...],                # Tespit edilen anormallikler
  "recommendations": [...],          # Terapi önerileri
  "final_output": "...",             # Son sonuç
  "metadata": {...}                  # Ek veriler
}
```

## 🔧 Özel Konfigürasyonlar

### LangSmith Aktivasyon (İsteğe Bağlı)

LangSmith'i etkinleştirmek için:

1. [LangSmith](https://www.langsmith.com) sitesine git
2. API anahtarı al
3. `.env`'ye ekle:
   ```env
   LANGSMITH_API_KEY=ls_...
   ```

Monitoring sistem otomatik olarak LangSmith'e veri gönderecektir.

### CrewAI Model Seçimi

`backend/app/crew_config/agents.yaml` dosyasında `llm_model` seçeneklerini değiştirebilirsiniz:
- `openai/gpt-4o` - Daha güçlü
- `openai/gpt-4-turbo` - Hızlı
- `openai/gpt-4o-mini` - Ekonomik (varsayılan)

## 📝 Örnek İmplementasyon

### Python SDK Kullanımı

```python
from app.workflow import get_workflow_executor
from app.crew_manager import get_crew_manager
from app.monitoring import get_monitor

# Workflow'ı çalıştır
executor = get_workflow_executor()
result = await executor.execute(
    child_id=1,
    child_name="Ahmet",
    parent_id=1,
    task_type="report",
    logs_data=logs_data,
    streaming=False
)

# İstatistikleri al
monitor = get_monitor()
stats = monitor.get_statistics()
print(f"Toplam etkinlik: {stats['total_events']}")
print(f"Toplam token: {stats['total_tokens']}")
```

## 🐳 Docker Kurulumu

```bash
# Docker Compose ile başlat
docker-compose up --build

# Backend servisini kontrol et
docker-compose ps
docker-compose logs backend

# Sağlığı kontrol et
curl http://localhost:8000/health
```

## 🚨 Sorun Giderme

### LangGraph Yükleme Hatası

```
ModuleNotFoundError: No module named 'langgraph'
```

**Çözüm:**
```bash
pip install langgraph==0.2.15
```

### CrewAI Konfigürasyonu Yüklenmedi

**Kontrol Et:**
```python
from app.crew_manager import get_crew_manager
manager = get_crew_manager()
print(manager.get_crew_info())
```

### Token Limiti Aşıldı

CrewAI görevleri çok fazla token kullanıyorsa:
1. Model'i değiştir (gpt-4o-mini → gpt-3.5-turbo)
2. Günlük veri sayısını azalt
3. Yapılandırma optimizasyonu

## 📚 İlgili Dosyalar

| Dosya | Amaç |
|-------|------|
| `app/state.py` | State yönetimi |
| `app/workflow.py` | LangGraph workflow |
| `app/workflow_nodes.py` | Workflow node'ları |
| `app/crew_manager.py` | CrewAI entegrasyonu |
| `app/monitoring.py` | İzleme sistemi |
| `app/services/enhanced_ai.py` | Yüksek seviye API'ler |
| `app/routers/ai.py` | HTTP endpoint'leri |

## 🤝 Katkı

Geliştirmeler ve hata düzeltmeleri için PR gönderin!

## 📄 Lisans

MIT License

---

**Daha fazla bilgi için:** [LangGraph Docs](https://docs.langchain.com/langgraph) | [CrewAI Docs](https://docs.crewai.com) | [LangSmith Docs](https://docs.smith.langchain.com)
