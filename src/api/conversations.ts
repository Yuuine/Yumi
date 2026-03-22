import { httpClient } from './http-client'

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
  async getConversations(
    userId: string,
    characterId?: string,
    limit = 20,
    offset = 0
  ): Promise<{ conversations: Conversation[] }> {
    return httpClient.get('/chat/conversations', {
      params: { userId, characterId, limit, offset },
    })
  },
}
