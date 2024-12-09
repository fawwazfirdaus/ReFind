import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
})

export interface Author {
  firstname: string
  lastname: string
  email?: string
  affiliation?: string
  orcid?: string
}

export interface Section {
  title: string
  content: string
}

export interface Reference {
  title: string
  authors: Author[]
  doi?: string
  year?: string
  abstract?: string
  venue?: string
}

export interface Paper {
  title: string
  authors: Author[]
  year?: string
  abstract?: string
  sections: Section[]
  references: Reference[]
}

export interface TokenUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export interface QueryResponse {
  answer: string
  metadata: {
    chunks_used: number
    token_usage: TokenUsage
    sources: string[]
  }
}

export const uploadPDF = async (file: File): Promise<Paper> => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getPaperDetails = async (): Promise<Paper> => {
  const response = await api.get('/paper')
  return response.data || { title: '', authors: [], sections: [], references: [] }
}

export const getReferences = async (): Promise<Reference[]> => {
  const response = await api.get('/references')
  return response.data || []
}

export const submitQuery = async (query: string): Promise<QueryResponse> => {
  const response = await api.post('/query', { text: query })
  return response.data
}

export default api 