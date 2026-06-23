import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface SessionResponse {
  session_id: string
  profile: {
    knowledge_level: number
    cognitive_field: string
    cognitive_modality: string
    learning_pace: string
    goal_orientation: string
    error_patterns: string[]
    mastered_concepts: string[]
  }
  target_concept: string | null
  suggested_path: string[]
}

export interface ChatRequest {
  message: string
  message_type?: string
}

export interface AgentResponse {
  agent_name: string
  response_type: string
  content: any
  profile_update?: any
  debate_report?: any
}

export interface GraphData {
  nodes: Array<{
    id: string
    name: string
    module: string
    difficulty: number
  }>
  edges: Array<{
    source: string
    target: string
    strength: number
  }>
}

export const sessionApi = {
  create: (target_concept?: string) =>
    api.post<SessionResponse>('/sessions/', { target_concept }),

  getProfile: (sessionId: string) =>
    api.get(`/sessions/${sessionId}/profile`),

  getStats: (sessionId: string) =>
    api.get(`/sessions/${sessionId}/stats`),

  chat: (sessionId: string, data: ChatRequest) =>
    api.post<AgentResponse>(`/sessions/${sessionId}/chat`, data),

  chatStream: (sessionId: string, message: string, messageType: string = 'text') =>
    fetch(`/api/sessions/${sessionId}/chat-stream?message=${encodeURIComponent(message)}&message_type=${messageType}`),
}

export const graphApi = {
  getGraph: () => api.get<GraphData>('/graph/'),
  getPath: (fromConcepts: string[], toConcept: string) =>
    api.get('/graph/path', {
      params: { from_concepts: fromConcepts.join(','), to_concept: toConcept },
    }),
  getConcept: (name: string) => api.get(`/graph/concept/${name}`),
}

export const resourceApi = {
  generate: (concept: string, profile?: any) =>
    api.post('/resources/generate', null, { params: { concept, profile } }),

  generateStream: (sessionId: string, concept: string) =>
    fetch(`/api/resources/stream-generate?session_id=${sessionId}&concept=${encodeURIComponent(concept)}`),
}

export default api
