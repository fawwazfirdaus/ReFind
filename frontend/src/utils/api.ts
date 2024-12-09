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
  status?: 'processed' | 'pending' | 'failed' | 'not_started'
}

export interface Paper {
  title: string
  authors: Author[]
  year?: string
  abstract?: string
  sections: Section[]
  references: Reference[]
  sourceContent?: string
}

export interface TokenUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export interface SourceInfo {
  text: string
  section: string
  start_line: number
  end_line: number
  similarity: number
}

export interface QueryResponse {
  answer: string
  metadata: {
    chunks_used: number
    token_usage: TokenUsage
    sources: SourceInfo[]
  }
}

export interface ReferenceStatus {
  references: { [key: string]: 'processed' | 'pending' | 'failed' | 'not_started' }
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

export const getReferencesStatus = async (): Promise<ReferenceStatus> => {
  const response = await api.get('/references/status')
  return response.data
}

export const submitQuery = async (query: string): Promise<QueryResponse> => {
  const response = await api.post('/query', { text: query })
  return response.data
}

// Reference API functions
export async function searchReferences(query: string, limit: number = 5) {
  const response = await fetch(`${API_BASE_URL}/references/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, limit }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to search references');
  }
  
  return response.json();
}

export async function getQueueStatus() {
  const response = await fetch(`${API_BASE_URL}/references/queue/status`);
  
  if (!response.ok) {
    throw new Error('Failed to get queue status');
  }
  
  return response.json();
}

export async function getReferenceContent(refId: string) {
  const response = await fetch(`${API_BASE_URL}/references/${refId}/content`);
  
  if (!response.ok) {
    throw new Error('Failed to get reference content');
  }
  
  return response.json();
}

export async function processReference(refId: string) {
  const response = await fetch(`${API_BASE_URL}/references/${refId}/process`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error('Failed to process reference');
  }
  
  return response.json();
}

export default api 