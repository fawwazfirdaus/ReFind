import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
})

export interface Reference {
  title: string
  authors: string[]
  doi?: string
  abstract?: string
}

export interface QueryResponse {
  answer: string
}

export const uploadPDF = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getReferences = async (): Promise<Reference[]> => {
  const response = await api.get('/references')
  return response.data.references
}

export const submitQuery = async (query: string): Promise<QueryResponse> => {
  const response = await api.post('/query', { text: query })
  return response.data
}

export default api 