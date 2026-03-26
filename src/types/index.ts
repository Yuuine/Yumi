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
  conversationId?: string
  message: string
  temperature?: number
  deepThinking?: boolean
  /** 当前账号下活跃角色卡 id，与后端 character_cards 对齐 */
  characterId?: string
}

export interface ChatResponse {
  reply: string
  emotion: EmotionData
  memoryUsed: number
  newSummary?: string
  conversationId?: string
}

export interface ChatHistory {
  messages: ChatMessage[]
}

export interface UserProfile {
  id: string
  roleName: string
  preferences: UserPreferences
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

export type ModelType = 'text' | 'image' | 'audio' | 'video'
export type TestStatus = 'untested' | 'passed' | 'failed'

export interface ModelConfig {
  id: string
  providerId: string
  name: string
  baseUrl: string
  apiKey: string
  modelName: string
  customModelName?: string
  modelType: ModelType
  maxTokens: number
  temperature: number
  isEnabled: boolean
  isTested: boolean
  testStatus: TestStatus
  lastTestAt?: string
  lastTestMessage?: string
  editCount: number
  createdAt?: string
  updatedAt?: string
}

export interface ModelTestRequest {
  baseUrl: string
  apiKey: string
  modelName: string
  testMessage?: string
}

export interface ModelTestResponse {
  success: boolean
  message: string
  response?: string
  reasoning?: string
  latency?: number
}

export interface Conversation {
  id: string
  accountId?: string
  characterId?: string
  title?: string
  messages: ChatMessage[]
  createdAt: string
  updatedAt: string
  isActive?: boolean
}
