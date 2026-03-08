import api from './client'

export interface Reminder {
  id: number
  child_id: number
  title: string
  reminder_type: string
  remind_at: string
  recur_type: string
  is_active: boolean
}

export const getReminders = (childId: number) => api.get<Reminder[]>(`/reminders/child/${childId}`)
export const createReminder = (data: Omit<Reminder, 'id'>) => api.post<Reminder>('/reminders', data)
export const updateReminder = (id: number, data: Partial<Reminder>) => api.put<Reminder>(`/reminders/${id}`, data)
export const deleteReminder = (id: number) => api.delete(`/reminders/${id}`)