import { describe, it, expect, vi, beforeEach } from 'vitest'
import { conversationsApi } from '@/api/conversations'

vi.mock('@/api/http-client', () => ({
  httpClient: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/utils/field-mapper', () => ({
  toConversationDTO: vi.fn(x => x),
  toConversationListDTO: vi.fn(x => x),
  conversationToBackend: vi.fn(x => x),
}))

import { httpClient } from '@/api/http-client'

describe('conversations.ts - 对话 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createConversation', () => {
    it('创建新对话', async () => {
      const mockResponse = { id: 'conv-123', userId: 'user-123' }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await conversationsApi.createConversation(
        'user-123',
        'char-123',
        'conv-123',
        '测试对话'
      )

      expect(httpClient.post).toHaveBeenCalled()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getConversations', () => {
    it('获取对话列表', async () => {
      const mockResponse = { conversations: [] }
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      const result = await conversationsApi.getConversations('user-123', 'char-123')

      expect(httpClient.get).toHaveBeenCalledWith('/conversations', {
        params: {
          userId: 'user-123',
          characterId: 'char-123',
          limit: 20,
          offset: 0,
        },
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateTitle', () => {
    it('更新对话标题', async () => {
      vi.mocked(httpClient.put).mockResolvedValue(undefined)

      await conversationsApi.updateTitle('conv-123', '新标题')

      expect(httpClient.put).toHaveBeenCalledWith('/conversations/conv-123/title', {
        title: '新标题',
      })
    })
  })

  describe('deleteConversation', () => {
    it('删除对话', async () => {
      vi.mocked(httpClient.delete).mockResolvedValue(undefined)

      await conversationsApi.deleteConversation('conv-123')

      expect(httpClient.delete).toHaveBeenCalledWith('/conversations/conv-123')
    })
  })
})
