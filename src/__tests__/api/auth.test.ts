import { describe, it, expect, vi, beforeEach } from 'vitest'
import { authApi } from '@/api/auth'

vi.mock('@/api/http-client', () => ({
  httpClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import { httpClient } from '@/api/http-client'

describe('auth.ts - 认证 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('发送登录请求', async () => {
      const mockResponse = {
        userId: 'user-123',
        accessToken: 'access-token',
        refreshToken: 'refresh-token',
        nickname: '测试用户',
      }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await authApi.login({
        nickname: 'test',
        password: 'password123',
      })

      expect(httpClient.post).toHaveBeenCalledWith('/auth/login', {
        nickname: 'test',
        password: 'password123',
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('register', () => {
    it('发送注册请求', async () => {
      const mockResponse = {
        userId: 'user-456',
        accessToken: 'access-token-2',
        refreshToken: 'refresh-token-2',
        nickname: '新用户',
      }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await authApi.register({
        nickname: 'newuser',
        password: 'password123',
      })

      expect(httpClient.post).toHaveBeenCalledWith('/auth/register', {
        nickname: 'newuser',
        password: 'password123',
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('refreshToken', () => {
    it('刷新令牌', async () => {
      const mockResponse = {
        userId: 'user-123',
        accessToken: 'new-access-token',
        refreshToken: 'new-refresh-token',
        nickname: '测试用户',
      }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await authApi.refreshToken('old-refresh-token')

      expect(httpClient.post).toHaveBeenCalledWith('/auth/refresh', {
        refreshToken: 'old-refresh-token',
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getCurrentUser', () => {
    it('获取当前用户信息', async () => {
      const mockResponse = {
        userId: 'user-123',
        nickname: '测试用户',
      }
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      const result = await authApi.getCurrentUser()

      expect(httpClient.get).toHaveBeenCalledWith('/auth/me')
      expect(result).toEqual(mockResponse)
    })
  })
})
