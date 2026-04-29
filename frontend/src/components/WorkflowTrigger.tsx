import { useState } from 'react'
import { useParams } from 'react-router-dom'
import type { WorkflowResponse } from '../api/ai'
import {
  generateWeeklyReport,
  chatWithAssistant,
  detectAnomalies,
  performDeepAnalysis,
  getMonitoringStats,
  getWorkflowInfo,
} from '../api/ai'

export function WorkflowTrigger() {
  const { childId } = useParams<{ childId: string }>()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<WorkflowResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedTask, setSelectedTask] = useState<'report' | 'chat' | 'anomaly' | 'analysis' | 'deep_analysis' | 'literature_review' | 'parent_support'>('report')
  const [chatQuery, setChatQuery] = useState('')
  const [showDetails, setShowDetails] = useState(false)

  const handleTaskChange = (task: string) => {
    setSelectedTask(task as 'report' | 'chat' | 'anomaly' | 'analysis')
    resetResult()
  }

  const resetResult = () => {
    setResult(null)
    setError(null)
  }

  const executeTask = async () => {
    if (!childId) {
      setError('Çocuk ID bulunamadı')
      return
    }

    setLoading(true)
    setError(null)
    resetResult()

    try {
      let response: WorkflowResponse

      switch (selectedTask) {
        case 'report':
          response = await generateWeeklyReport(parseInt(childId))
          break
        case 'chat':
          if (!chatQuery.trim()) {
            setError('Lütfen bir soru girin')
            setLoading(false)
            return
          }
          response = await chatWithAssistant(parseInt(childId), chatQuery)
          setChatQuery('')
          break
        case 'anomaly':
          response = await detectAnomalies(parseInt(childId))
          break
        case 'analysis':
          response = await performDeepAnalysis(parseInt(childId))
          break
        default:
          setError('Bilinmeyen görev türü')
          setLoading(false)
          return
      }

      if (response.success) {
        setResult(response)
      } else {
        setError(response.error || 'İşlem başarısız oldu')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata oluştu')
    } finally {
      setLoading(false)
    }
  }

  const loadSystemInfo = async () => {
    try {
      const info = await getWorkflowInfo()
      console.log('Workflow Info:', info)
      alert('Sistem bilgileri konsola yazdırıldı')
    } catch (err) {
      setError('Sistem bilgileri yüklenemedi')
    }
  }

  const loadStats = async () => {
    try {
      const stats = await getMonitoringStats()
      console.log('Monitoring Stats:', stats)
      alert('İzleme istatistikleri konsola yazdırıldı')
    } catch (err) {
      setError('İstatistikler yüklenemedi')
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">🤖 AI Hibrit Workflow Sistemi</h2>

      {/* Görev Seçimi */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Görev Türü</label>
        <div className="grid grid-cols-2 gap-3">
          {[
            { id: 'report', label: '📋 Haftalık Rapor', desc: 'Kapsamlı analiz raporu' },
            { id: 'chat', label: '💬 Sohbet', desc: 'Ebeveyn soruları' },
            { id: 'anomaly', label: '🔍 Anomali Tespiti', desc: 'Anormal davranışlar' },
            { id: 'analysis', label: '🧬 Derinlemesine Analiz', desc: 'Detaylı inceleme' },
            { id: 'deep_analysis', label: '📈 İstatistiksel Analiz', desc: 'Korelasyon ve trendler' },
            { id: 'literature_review', label: '📚 Literatür Araştırması', desc: 'Güncel akademik kaynaklar' },
            { id: 'parent_support', label: '💛 Ebeveyn Desteği', desc: 'Pratik stratejiler' },
          ].map((task) => (
            <button
              key={task.id}
              onClick={() => handleTaskChange(task.id)}
              className={`p-3 rounded-lg transition-all ${
                selectedTask === task.id
                  ? 'bg-blue-500 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <div className="font-semibold">{task.label}</div>
              <div className="text-xs opacity-75">{task.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Sohbet Giriş */}
      {selectedTask === 'chat' && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Sorunuz</label>
          <textarea
            value={chatQuery}
            onChange={(e) => setChatQuery(e.target.value)}
            placeholder="Ahmet bu hafta nasıl geçti? Yeni tavırlar görüyor musunuz?"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
          />
        </div>
      )}

      {/* Hata Mesajı */}
      {error && (
        <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          <strong>Hata:</strong> {error}
        </div>
      )}

      {/* Yükleniyor */}
      {loading && (
        <div className="mb-6 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded-lg">
          <div className="flex items-center">
            <div className="animate-spin mr-3">⏳</div>
            <span>AI işleme devam ediyor... ({selectedTask})</span>
          </div>
        </div>
      )}

      {/* Sonuç */}
      {result && (
        <div className="mb-6 p-4 bg-green-100 border border-green-400 rounded-lg">
          <div className="mb-4">
            <h3 className="font-bold text-lg text-green-800">✅ İşlem Başarılı</h3>
            <p className="text-sm text-green-700">Durum: {result.status}</p>
            <p className="text-sm text-green-700">Süre: {result.execution_time.toFixed(2)} saniye</p>
            {result.confidence_score != null && (
              <p className="text-sm text-green-700">
                Güven Skoru: {Math.round(result.confidence_score * 100)}%
              </p>
            )}
            {result.needs_human_review && (
              <p className="text-sm text-amber-700 font-semibold mt-1">
                ⏳ İnsan onayı bekleniyor — AI Onay Paneli'ni kontrol edin
              </p>
            )}
          </div>

          {/* Çıktı */}
          {result.output && (
            <div className="bg-white p-3 rounded border border-green-300 mb-3 max-h-48 overflow-y-auto">
              <div className="text-sm whitespace-pre-wrap font-mono text-gray-800">
                {result.output.substring(0, 500)}...
              </div>
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="text-blue-600 hover:text-blue-800 text-sm mt-2 underline"
              >
                {showDetails ? 'Gizle' : 'Tümünü Göster'}
              </button>
            </div>
          )}

          {/* Detaylar */}
          {showDetails && (
            <div className="bg-gray-50 p-3 rounded border border-gray-300 text-xs">
              <p className="font-mono whitespace-pre-wrap text-gray-700">
                {JSON.stringify(
                  {
                    analysis: result.analysis,
                    anomalies: result.anomalies,
                    recommendations: result.recommendations,
                  },
                  null,
                  2
                )}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Butonlar */}
      <div className="flex gap-3">
        <button
          onClick={executeTask}
          disabled={loading}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50"
        >
          {loading ? '⏳ İşleniyor...' : '🚀 Çalıştır'}
        </button>

        <button
          onClick={loadSystemInfo}
          disabled={loading}
          className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50"
        >
          ℹ️ Sistem Bilgi
        </button>

        <button
          onClick={loadStats}
          disabled={loading}
          className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50"
        >
          📊 İstatistikler
        </button>
      </div>

      {/* Bilgi */}
      <div className="mt-6 p-4 bg-gray-50 rounded border border-gray-200 text-sm">
        <p className="text-gray-600">
          <strong>Çocuk ID:</strong> {childId || 'Bilinmiyor'}
        </p>
        <p className="text-gray-600 mt-1">
          <strong>Seçili Görev:</strong> {selectedTask}
        </p>
      </div>
    </div>
  )
}
