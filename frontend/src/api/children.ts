import api from './client'

export interface Child {
  id: number
  name: string
  birth_date: string
  notes?: string
}

export const getChildren = () => api.get<Child[]>('/children')
export const createChild = (data: { name: string; birth_date: string; notes?: string }) => api.post<Child>('/children', data)
export const updateChild = (id: number, data: Partial<Child>) => api.put<Child>(`/children/${id}`, data)
export const deleteChild = (id: number) => api.delete(`/children/${id}`)