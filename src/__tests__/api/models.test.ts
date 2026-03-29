import { describe, it, expect, vi, beforeEach } from 'vitest'
import { modelsApi } from '@/api/models'

vi.mock('@/api/http-client', () => ({
  httpClient: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import { httpClient } from '@/api/http-client'

describe('models.ts - 模型 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getModels', () => {
    it('获取模型列表', async () => {
      const mockResponse = [{ id: 'model-1', name: 'GPT-4' }]
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      const result = await modelsApi.getModels('acc-123')

      expect(httpClient.get).toHaveBeenCalledWith('/models', {
        params: { accountId: 'acc-123' },
      })
      expect(result.length).toBe(1)
    })
  })

  describe('createModel', () => {
    it('创建模型配置', async () => {
      const mockResponse = {
        id: 'new-model',
        name: '测试模型',
        providerId: 'openai',
        baseUrl: 'https://api.openai.com',
        apiKey: 'sk-...',
        modelName: 'gpt-4',
      }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await modelsApi.createModel('acc-123', {
        name: '测试模型',
        providerId: 'openai',
        baseUrl: 'https://api.openai.com',
        apiKey: 'sk-...',
        modelName: 'gpt-4',
      } as any)

      expect(httpClient.post).toHaveBeenCalled()
      expect(result.id).toBe('new-model')
      expect(result.name).toBe('测试模型')
    })
  })

  describe('updateModel', () => {
    it('更新模型配置', async () => {
      const mockResponse = {
        id: 'model-1',
        name: '更新的模型',
      }
      vi.mocked(httpClient.put).mockResolvedValue(mockResponse)

      const result = await modelsApi.updateModel('acc-123', 'model-1', {
        name: '更新的模型',
      })

      expect(httpClient.put).toHaveBeenCalled()
      expect(result.id).toBe('model-1')
      expect(result.name).toBe('更新的模型')
    })
  })

  describe('deleteModel', () => {
    it('删除模型配置', async () => {
      vi.mocked(httpClient.delete).mockResolvedValue(undefined)

      await modelsApi.deleteModel('acc-123', 'model-1')

      expect(httpClient.delete).toHaveBeenCalledWith('/models/model-1', {
        params: { accountId: 'acc-123' },
      })
    })
  })

  describe('enableModel', () => {
    it('启用模型', async () => {
      const mockResponse = { success: true, message: 'Enabled' }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await modelsApi.enableModel('acc-123', 'model-1')

      expect(httpClient.post).toHaveBeenCalled()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('disableModel', () => {
    it('禁用模型', async () => {
      const mockResponse = { success: true, message: 'Disabled' }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await modelsApi.disableModel('acc-123', 'model-1')

      expect(httpClient.post).toHaveBeenCalled()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('setActiveModel', () => {
    it('设置激活模型', async () => {
      const mockResponse = { success: true, message: 'Active' }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await modelsApi.setActiveModel('acc-123', 'model-1')

      expect(httpClient.post).toHaveBeenCalled()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('testModel', () => {
    it('测试模型连接', async () => {
      const mockResponse = { success: true }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await modelsApi.testModel({
        baseUrl: 'https://api.openai.com',
        apiKey: 'sk-...',
        modelName: 'gpt-4',
        testMessage: 'Hello',
      } as any)

      expect(httpClient.post).toHaveBeenCalled()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('testModelById', () => {
    it('通过ID测试模型', async () => {
      const mockResponse = { success: true, message: 'Success' }
      vi.mocked(httpClient.post).mockResolvedValue(mockResponse)

      const result = await modelsApi.testModelById('acc-123', 'model-1')

      expect(httpClient.post).toHaveBeenCalled()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getActiveModel', () => {
    it('获取激活模型', async () => {
      const mockResponse = { id: 'active-model', name: 'Active Model' }
      vi.mocked(httpClient.get).mockResolvedValue(mockResponse)

      const result = await modelsApi.getActiveModel('acc-123')

      expect(httpClient.get).toHaveBeenCalledWith('/active', {
        params: { accountId: 'acc-123' },
      })
      expect(result).not.toBeNull()
    })

    it('无激活模型时返回null', async () => {
      vi.mocked(httpClient.get).mockResolvedValue(null)

      const result = await modelsApi.getActiveModel('acc-123')

      expect(result).toBeNull()
    })
  })
})
