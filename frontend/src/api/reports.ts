import api from './client'

export interface WeeklyReport {
  id: number
  child_id: number
  week_start_date: string
  report_text: string
  key_insights: { en_iyi_gun: string; gelisim_alani: string; dikkat_alani: string }
  recommendations: string[]
}

export const getReports = (childId: number) => api.get<WeeklyReport[]>(`/reports/child/${childId}`)
export const generateReport = (childId: number, weekStart: string) =>
  api.post<WeeklyReport>(`/reports/generate/${childId}?week_start=${weekStart}`)