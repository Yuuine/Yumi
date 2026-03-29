import { describe, it, expect, vi, beforeEach } from 'vitest'
import { chatApi } from '@/api/chat'

vi.mock('@/api/http-client', () => ({
  httpClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import { httpClient } from '@/api/http-client'

describe('chat.ts - 聊天 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('sendMessage', () => {
    it('发送聊天消息', async () => {
      const mockResponse = {
        reply: 'Hello!',
        conversationId: 'conv-123',
        emotion: { valence: 0.5, arousal: 0.5 },
      }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const request = {
        userId: 'user-123',
        message: 'Hi',
      } as any

      const result = await chatApi.sendMessage(request)

      expect(httpClient.post).toHaveBeenCalledWith('/chat', request)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getHistory', () => {
    it('获取聊天历史记录', async () => {
      const mockResponse = {
        messages: [],
        hasMore: false,
      }
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      const result = await chatApi.getHistory('user-123', 50, 0, 'conv-123')

      expect(httpClient.get).toHaveBeenCalledWith('/chat/history', {
        params: {
          userId: 'user-123',
          limit: 50,
          offset: 0,
          conversationId: 'conv-123',
        },
      })
      expect(result).toEqual(mockResponse)
    })

    it('获取历史记录时可选参数可以省略', async () => {
      const mockResponse = {
        messages: [],
        hasMore: false,
      }
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      await chatApi.getHistory('user-123')

      expect(httpClient.get).toHaveBeenCalledWith('/chat/history', {
        params: {
          userId: 'user-123',
          limit: 50,
          offset: 0,
        },
      })
    })
  })
})
