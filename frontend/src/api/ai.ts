import api from './client'

// ============================================================================
// KLASIK ENDPOINT'LER (UYUMLU)
// ============================================================================

export const sendChatMessage = (childId: number, message: string) =>
  api.post(`/ai/chat/${childId}`, { message })


//stream fonksiyonu
export const streamAdvisorMessage = (
  childId: number,
  message: string,
  handlers: {
    onStart?: () => void
    onChunk: (text: string) => void
    onDone?: (payload?: Record<string, unknown>) => void
    onError?: (error: Error) => void
  },
  scheduleTimeIso?: string
) => {
  const token = localStorage.getItem('token')
  if (!token) {
    handlers.onError?.(new Error('Token bulunamadı. Lütfen tekrar giriş yapın.'))
    return () => {}
  }

  const baseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
  const url = new URL(`${baseUrl}/mcp/advisor/stream`)
  url.searchParams.set('token', token)
  url.searchParams.set('child_id', String(childId))
  url.searchParams.set('message', message)
  if (scheduleTimeIso) {
    url.searchParams.set('schedule_time_iso', scheduleTimeIso)
  }

  const eventSource = new EventSource(url.toString())

  eventSource.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (payload.type === 'start') handlers.onStart?.()
      if (payload.type === 'chunk' && typeof payload.text === 'string') handlers.onChunk(payload.text)
      if (payload.type === 'done') {
        handlers.onDone?.(payload.tool_result)
        eventSource.close()
      }
    } catch (error) {
      handlers.onError?.(error as Error)
      eventSource.close()
    }
  }

  eventSource.onerror = () => {
    handlers.onError?.(new Error('Canli yanit akisi kesildi.'))
    eventSource.close()
  }

  return () => eventSource.close()
}

export const checkAnomaly = (childId: number) =>
  api.get(`/ai/anomaly/${childId}`)

// ============================================================================
// YENİ LANGGRAPH WORKFLOW ENDPOINT'LERİ (v2)
// ============================================================================

export interface WorkflowRequest {
  task_type: 'report' | 'chat' | 'anomaly' | 'analysis' | 'deep_analysis' | 'literature_review' | 'parent_support'
  query?: string
  streaming?: boolean
}

export interface WorkflowResponse {
  success: boolean
  status: string
  output: string
  analysis?: Record<string, any>
  anomalies?: Array<Record<string, any>>
  recommendations?: string[]
  execution_time: number
  error?: string
  // Yeni alanlar
  needs_human_review?: boolean
  human_review_status?: string
  confidence_score?: number
  search_results?: Array<Record<string, any>>
  literature_findings?: string
}

/**
 * LangGraph + CrewAI Workflow'u Çalıştır
 * Task Types:
 * - "report": Haftalık AI raporu oluştur
 * - "chat": Ebeveyn sorusuna cevap ver
 * - "anomaly": Anormal davranış tespiti
 * - "analysis": Derinlemesine davranış analizi
 */
export const executeWorkflow = async (
  childId: number,
  request: WorkflowRequest
): Promise<WorkflowResponse> => {
  try {
    const { data } = await api.post<WorkflowResponse>(
      `/ai/v2/workflow/${childId}`,
      request
    )
    return data
  } catch (error) {
    console.error('Workflow hatası:', error)
    throw error
  }
}

/**
 * İş Akışı Bilgilerini Al
 */
export const getWorkflowInfo = async () => {
  try {
    const { data } = await api.get('/ai/v2/workflow/info')
    return data
  } catch (error) {
    console.error('Workflow bilgileri hatası:', error)
    throw error
  }
}

/**
 * İzleme İstatistiklerini Al
 */
export const getMonitoringStats = async () => {
  try {
    const { data } = await api.get('/ai/v2/monitoring/stats')
    return data
  } catch (error) {
    console.error('Monitoring istatistikleri hatası:', error)
    throw error
  }
}

/**
 * Sistem Sağlığını Kontrol Et
 */
export const checkSystemHealth = async () => {
  try {
    const { data } = await api.get('/ai/health')
    return data
  } catch (error) {
    console.error('Sistem sağlığı hatası:', error)
    throw error
  }
}

/**
 * Doğrudan CrewAI Ekipini Çalıştır
 * Crew Types: "analysis" | "anomaly" | "recommendations" | "report" | "chat"
 */
export const executeCrewDirectly = async (
  crewType: 'analysis' | 'anomaly' | 'recommendations' | 'report' | 'chat',
  childId: number
) => {
  try {
    const { data } = await api.post(`/ai/v2/crew/${crewType}/${childId}`)
    return data
  } catch (error) {
    console.error('Crew çalıştırma hatası:', error)
    throw error
  }
}

/**
 * Haftalık Rapor Oluştur
 */
export const generateWeeklyReport = async (childId: number) => {
  return executeWorkflow(childId, {
    task_type: 'report',
    streaming: false,
  })
}

/**
 * Anomali Tespiti (Geliştirilmiş)
 */
export const detectAnomalies = async (childId: number) => {
  return executeWorkflow(childId, {
    task_type: 'anomaly',
    streaming: false,
  })
}

/**
 * Ebeveyn Sohbeti (Geliştirilmiş)
 */
export const chatWithAssistant = async (childId: number, query: string) => {
  return executeWorkflow(childId, {
    task_type: 'chat',
    query,
    streaming: false,
  })
}

/**
 * Derinlemesine Davranış Analizi
 */
export const performDeepAnalysis = async (childId: number) => {
  return executeWorkflow(childId, {
    task_type: 'analysis',
    streaming: false,
  })
}

/**
 * İstatistiksel Derin Analiz (DataAnalystAgent)
 * NEDEN: Korelasyonlar, zaman serisi trendleri ve uzun vadeli desenler
 */
export const performStatisticalAnalysis = async (childId: number) => {
  return executeWorkflow(childId, {
    task_type: 'deep_analysis',
    streaming: false,
  })
}

/**
 * Literatür Araştırması (LiteratureReviewAgent)
 * NEDEN: Güncel akademik kaynakları tarayarak bilimsel dayanak sağlar
 */
export const performLiteratureReview = async (childId: number) => {
  return executeWorkflow(childId, {
    task_type: 'literature_review',
    streaming: false,
  })
}

/**
 * Ebeveyn Destek (ParentSupportAgent)
 * NEDEN: Pratik günlük stratejiler ve empatik rehberlik
 */
export const getParentSupport = async (childId: number, query?: string) => {
  return executeWorkflow(childId, {
    task_type: 'parent_support',
    query,
    streaming: false,
  })
}

// ============================================================================
// HUMAN-IN-THE-LOOP (HITL) API
// ============================================================================

export interface HumanReview {
  id: number
  workflow_id: string
  task_type: string
  ai_output: string
  confidence_score?: number
  status: string
  reviewer_notes?: string
  modified_output?: string
  created_at?: string
  reviewed_at?: string
}

/**
 * Onay Bekleyen Çıktıları Al
 */
export const getPendingReviews = async (childId: number): Promise<HumanReview[]> => {
  try {
    const { data } = await api.get<HumanReview[]>(`/ai/v2/reviews/${childId}`)
    return data
  } catch (error) {
    console.error('Onay listesi hatası:', error)
    throw error
  }
}

/**
 * Tüm Onay Geçmişini Al
 */
export const getAllReviews = async (childId: number): Promise<HumanReview[]> => {
  try {
    const { data } = await api.get<HumanReview[]>(`/ai/v2/reviews/all/${childId}`)
    return data
  } catch (error) {
    console.error('Onay geçmişi hatası:', error)
    throw error
  }
}

/**
 * Onay Durumunu Güncelle
 */
export const updateReview = async (
  reviewId: number,
  status: 'approved' | 'rejected' | 'modified',
  reviewerNotes?: string,
  modifiedOutput?: string,
) => {
  try {
    const { data } = await api.put(`/ai/v2/reviews/${reviewId}`, {
      status,
      reviewer_notes: reviewerNotes,
      modified_output: modifiedOutput,
    })
    return data
  } catch (error) {
    console.error('Onay güncelleme hatası:', error)
    throw error
  }
}

/**
 * İzleme Verilerini Sıfırla
 */
export const resetMonitoring = async () => {
  try {
    const { data } = await api.post('/ai/reset-monitoring')
    return data
  } catch (error) {
    console.error('Monitoring sıfırlama hatası:', error)
    throw error
  }
}
