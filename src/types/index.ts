export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  emotion?: EmotionData
}

export interface EmotionData {
  valence: number
  arousal: number
}

export interface ChatRequest {
  userId: string
  message: string
  temperature?: number
}

export interface ChatResponse {
  reply: string
  emotion: EmotionData
  memoryUsed: number
  newSummary?: string
}

export interface ChatHistory {
  messages: ChatMessage[]
}

export interface UserProfile {
  id: string
  roleName: string
  bigFive: BigFiveTraits
  preferences: UserPreferences
}

export interface BigFiveTraits {
  openness: number
  conscientiousness: number
  extraversion: number
  agreeableness: number
  neuroticism: number
}

export interface UserPreferences {
  communicationStyle: string
  topicsOfInterest: string[]
  emotionalSupportLevel: string
  responseLength: string
}

export interface AppSettings {
  apiEndpoint: string
  apiKey: string
  modelName: string
  maxTokens: number
  temperature: number
  memoryEnabled: boolean
  emotionDetection: boolean
  theme: 'light' | 'dark'
  language: string
}

export interface MemoryItem {
  id: string
  content: string
  timestamp: string
  similarity: number
  decayFactor: number
}

export interface MemorySearchResult {
  memories: MemoryItem[]
  total: number
}

export interface MemoryStats {
  totalMemories: number
  oldestMemory?: string
  newestMemory?: string
  avgImportance: number
}
