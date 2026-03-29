import { describe, it, expect, vi, beforeEach } from 'vitest'
import { characterCardsApi } from '@/api/character-cards'

vi.mock('@/api/http-client', () => ({
  httpClient: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/utils/field-mapper', () => ({
  toCharacterCardListDTO: vi.fn(x => x),
  characterCardToBackend: vi.fn(x => x),
}))

vi.mock('@/utils/api-cache', () => ({
  apiCache: {
    invalidatePattern: vi.fn(),
  },
}))

import { httpClient } from '@/api/http-client'
import { apiCache } from '@/utils/api-cache'

describe('character-cards.ts - 角色卡 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('list', () => {
    it('列出角色卡', async () => {
      const mockResponse = []
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      const result = await characterCardsApi.list('user-123')

      expect(httpClient.get).toHaveBeenCalledWith('/character-cards', {
        params: { userId: 'user-123' },
        cache: true,
        ttl: 120000,
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('upsert', () => {
    it('更新或创建角色卡', async () => {
      const mockResponse = { success: true }
      vi.mocked(httpClient.put).mockResolvedValue(mockResponse)

      const result = await characterCardsApi.upsert('user-123', 'card-123', {
        id: 'card-123',
        name: '测试角色',
      } as any)

      expect(httpClient.put).toHaveBeenCalled()
      expect(apiCache.invalidatePattern).toHaveBeenCalledWith('GET:/character-cards')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('batchUpsert', () => {
    it('批量更新或创建角色卡', async () => {
      const mockResponse = { success: true, count: 2 }
      vi.mocked(httpClient.put).mockResolvedValue(mockResponse)

      const result = await characterCardsApi.batchUpsert('user-123', [
        { id: 'card-1', name: '角色1' } as any,
        { id: 'card-2', name: '角色2' } as any,
      ])

      expect(httpClient.put).toHaveBeenCalled()
      expect(apiCache.invalidatePattern).toHaveBeenCalledWith('GET:/character-cards')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('remove', () => {
    it('删除角色卡', async () => {
      const mockResponse = { success: true }
      vi.mocked(httpClient.delete).mockResolvedValue(mockResponse)

      const result = await characterCardsApi.remove('user-123', 'card-123')

      expect(httpClient.delete).toHaveBeenCalled()
      expect(apiCache.invalidatePattern).toHaveBeenCalledWith('GET:/character-cards')
      expect(result).toEqual(mockResponse)
    })
  })
})
