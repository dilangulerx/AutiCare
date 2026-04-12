import api from './client'

// ============================================================================
// KLASIK ENDPOINT'LER (UYUMLU)
// ============================================================================

export const sendChatMessage = (childId: number, message: string) =>
  api.post(`/ai/chat/${childId}`, { message })

export const checkAnomaly = (childId: number) =>
  api.get(`/ai/anomaly/${childId}`)

// ============================================================================
// YENİ LANGGRAPH WORKFLOW ENDPOINT'LERİ (v2)
// ============================================================================

export interface WorkflowRequest {
  task_type: 'report' | 'chat' | 'anomaly' | 'analysis'
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
