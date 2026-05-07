import api from './client'

export interface DailyLog {
  id: number
  child_id: number
  date: string
  eye_contact?: number
  aggression_level?: number
  communication_score?: number
  sleep_hours?: number
  sleep_start_time?: string
  sleep_end_time?: string
  sleep_interruptions?: number
  eye_contact_frequency?: number
  eye_contact_duration_seconds?: number
  eye_contact_context?: string
  aggression_frequency?: number
  aggression_duration_minutes?: number
  aggression_trigger?: string
  communication_mode?: 'verbal' | 'non_verbal' | 'mixed'
  communication_function?: string
  communication_effectiveness?: number
  antecedent?: string
  behavior?: string
  consequence?: string
  sensory_trigger?: string
  gi_notes?: string
  notes?: string
}

export const getLogs = (childId: number) => api.get<DailyLog[]>(`/logs/child/${childId}`)
export const getLogByDate = (childId: number, date: string) => api.get<DailyLog>(`/logs/child/${childId}/date/${date}`)

const normalizeEmptyStrings = <T extends Record<string, unknown>>(payload: T): T => {
  const next = { ...payload }
  Object.keys(next).forEach((key) => {
    const value = next[key]
    if (typeof value === 'string' && value.trim() === '') {
      ;(next as Record<string, unknown>)[key] = undefined
    }
  })
  return next
}

export const createLog = (data: Omit<DailyLog, 'id'>) =>
  api.post<DailyLog>('/logs', normalizeEmptyStrings(data))

export const updateLog = (id: number, data: Partial<DailyLog>) => api.put<DailyLog>(`/logs/${id}`, data)