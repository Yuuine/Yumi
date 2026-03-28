import { httpClient } from './http-client'
import {
  toConversationDTO,
  toConversationListDTO,
  conversationToBackend,
} from '@/utils/field-mapper'

export interface Conversation {
  id: string
  userId?: string
  characterId?: string
  title?: string
  createdAt?: string
  updatedAt?: string
  isActive?: boolean
}

export const conversationsApi = {
  async createConversation(
    userId: string,
    characterId?: string,
    conversationId?: string,
    title = '新对话'
  ): Promise<Conversation> {
    const data = conversationToBackend({
      id: conversationId,
      userId,
      characterId,
      title,
    })
    const response = await httpClient.post<Record<string, unknown>>('/conversations', data)
    return toConversationDTO(response) as Conversation
  },

  async getConversations(
    userId: string,
    characterId?: string,
    limit = 20,
    offset = 0
  ): Promise<{ conversations: Conversation[] }> {
    const response = await httpClient.get<{ conversations: Record<string, unknown>[] }>(
      '/conversations',
      {
        params: { userId, characterId, limit, offset },
      }
    )
    return {
      conversations: toConversationListDTO(response.conversations) as Conversation[],
    }
  },

  async updateTitle(conversationId: string, title: string): Promise<void> {
    return httpClient.put(`/conversations/${conversationId}/title`, { title })
  },

  async deleteConversation(conversationId: string): Promise<void> {
    return httpClient.delete(`/conversations/${conversationId}`)
  },
}
