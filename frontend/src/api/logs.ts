import api from './client'

export interface DailyLog {
  id: number
  child_id: number
  date: string
  eye_contact: number
  aggression_level: number
  communication_score: number
  sleep_hours: number
  notes?: string
}

export const getLogs = (childId: number) => api.get<DailyLog[]>(`/logs/child/${childId}`)
export const getLogByDate = (childId: number, date: string) => api.get<DailyLog>(`/logs/child/${childId}/date/${date}`)
export const createLog = (data: Omit<DailyLog, 'id'>) => api.post<DailyLog>('/logs', data)
export const updateLog = (id: number, data: Partial<DailyLog>) => api.put<DailyLog>(`/logs/${id}`, data)