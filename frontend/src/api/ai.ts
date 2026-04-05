import api from './client'

export const sendChatMessage = (childId: number, message: string) =>
  api.post(`/ai/chat/${childId}`, { message })

export const checkAnomaly = (childId: number) =>
    api.get(`/ai/anomaly/${childId}`)