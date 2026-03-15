import type { ChatRequest, ChatResponse, ChatHistory } from '@/types'
import { httpClient } from './http-client'

export const chatApi = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return httpClient.post<ChatResponse>('/chat', request)
  },

  async getHistory(userId: string, limit = 50): Promise<ChatHistory> {
    return httpClient.get<ChatHistory>('/chat/history', {
      params: { userId, limit },
    })
  },
}
