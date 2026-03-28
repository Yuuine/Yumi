import type { ChatRequest, ChatResponse, ChatHistory } from '@/types'
import { httpClient } from './http-client'

export const chatApi = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return httpClient.post<ChatResponse>('/chat', request)
  },

  async getHistory(
    userId: string,
    limit = 50,
    offset = 0,
    conversationId?: string
  ): Promise<ChatHistory> {
    const params: Record<string, unknown> = { userId, limit, offset }
    if (conversationId) {
      params.conversationId = conversationId
    }
    return httpClient.get<ChatHistory>('/chat/history', { params })
  },
}
