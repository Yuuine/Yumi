import { describe, it, expect, vi, beforeEach } from 'vitest'
import { userApi } from '@/api/user'

vi.mock('@/api/http-client', () => ({
  httpClient: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
  },
}))

vi.mock('@/utils/api-cache', () => ({
  apiCache: {
    invalidatePattern: vi.fn(),
  },
}))

import { httpClient } from '@/api/http-client'
import { apiCache } from '@/utils/api-cache'

describe('user.ts - 用户 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listUsers', () => {
    it('获取用户列表', async () => {
      const mockResponse = {
        users: [
          { id: 'user-1', roleName: '测试用户', createdAt: '2024-01-01', updatedAt: '2024-01-02' },
        ],
      }
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      const result = await userApi.listUsers()

      expect(httpClient.get).toHaveBeenCalledWith('/user/list')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getFullAccountData', () => {
    it('获取完整账户数据', async () => {
      const mockResponse = {
        id: 'user-1',
        roleName: '测试用户',
        preferences: {
          communicationStyle: 'friendly',
          topicsOfInterest: ['AI', 'tech'],
          emotionalSupportLevel: 'medium',
          responseLength: 'medium',
        },
        createdAt: '2024-01-01',
        updatedAt: '2024-01-02',
        characterCards: [],
        conversations: [],
      }
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      const result = await userApi.getFullAccountData('user-1')

      expect(httpClient.get).toHaveBeenCalled()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getProfile', () => {
    it('获取用户资料', async () => {
      const mockResponse = {
        userId: 'user-1',
        nickname: '测试用户',
      }
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      const result = await userApi.getProfile('user-1')

      expect(httpClient.get).toHaveBeenCalledWith('/user/profile', {
        params: { userId: 'user-1' },
        cache: true,
        ttl: 300000,
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateProfile', () => {
    it('更新用户资料', async () => {
      const mockResponse = {
        userId: 'user-1',
        nickname: '更新的用户',
      }
      vi.mocked(httpClient.put).mockResolvedValue(mockResponse)

      const result = await userApi.updateProfile({
        userId: 'user-1',
        nickname: '更新的用户',
      } as any)

      expect(httpClient.put).toHaveBeenCalledWith('/user/profile', {
        userId: 'user-1',
        nickname: '更新的用户',
      })
      expect(apiCache.invalidatePattern).toHaveBeenCalledWith('GET:/user/profile')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('purgeUserData', () => {
    it('清除用户数据', async () => {
      const mockResponse = {
        success: true,
        cleared: { messages: 10, conversations: 2 },
      }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await userApi.purgeUserData('user-1')

      expect(httpClient.post).toHaveBeenCalledWith('/user/purge', { userId: 'user-1' })
      expect(result).toEqual(mockResponse)
    })
  })
})
