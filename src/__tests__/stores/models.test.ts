import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useModelsStore } from '@/stores/models'

vi.mock('@/api/models', () => ({
  modelsApi: {
    getModels: vi.fn(),
    getActiveModel: vi.fn(),
    createModel: vi.fn(),
    updateModel: vi.fn(),
    deleteModel: vi.fn(),
    enableModel: vi.fn(),
    disableModel: vi.fn(),
    setActiveModel: vi.fn(),
    testModelById: vi.fn(),
  },
}))

vi.mock('@/utils/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}))

vi.mock('@/stores/account', () => ({
  useAccountStore: vi.fn(() => ({
    currentAccountId: 'test-account-id',
  })),
}))

import { modelsApi } from '@/api/models'
import type { ModelConfig, ModelTestResponse } from '@/types'

const mockModel: ModelConfig = {
  id: 'model-1',
  providerId: 'provider-1',
  name: 'Test Model',
  baseUrl: 'https://api.example.com',
  apiKey: 'test-api-key',
  modelName: 'gpt-4',
  modelType: 'text',
  maxTokens: 4096,
  temperature: 0.7,
  isEnabled: true,
  isTested: true,
  testStatus: 'passed',
  editCount: 0,
}

const mockTestResponse: ModelTestResponse = {
  success: true,
  message: '测试成功',
  response: 'Test response',
  reasoning: 'Test reasoning',
  latency: 123,
}

describe('useModelsStore - 模型 Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('基础状态', () => {
    it('初始化状态正确', () => {
      const store = useModelsStore()

      expect(store.models).toEqual([])
      expect(store.activeModel).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.isTesting).toBe(false)
      expect(store.testResult).toBeNull()
    })

    it('enabledModels 计算属性正确过滤', () => {
      const store = useModelsStore()

      store.models = [
        { id: '1', name: 'Model 1', isEnabled: true, apiKey: 'key-1' } as any,
        { id: '2', name: 'Model 2', isEnabled: false, apiKey: 'key-2' } as any,
        { id: '3', name: 'Model 3', isEnabled: true, apiKey: '' } as any,
      ]

      expect(store.enabledModels.length).toBe(1)
      expect(store.enabledModels[0].id).toBe('1')
    })
  })

  describe('getRequiredAccountId', () => {
    it('返回当前账号 ID', () => {
      const store = useModelsStore()
      expect(store.getRequiredAccountId()).toBe('test-account-id')
    })
  })

  describe('loadModels', () => {
    it('成功加载模型列表', async () => {
      const store = useModelsStore()
      const mockModels = [mockModel]
      vi.mocked(modelsApi.getModels).mockResolvedValue(mockModels)

      await store.loadModels()

      expect(modelsApi.getModels).toHaveBeenCalledWith('test-account-id')
      expect(store.models).toEqual(mockModels)
    })

    it('加载失败时清空模型列表', async () => {
      const store = useModelsStore()
      store.models = [mockModel]
      vi.mocked(modelsApi.getModels).mockRejectedValue(new Error('API Error'))

      await store.loadModels()

      expect(store.models).toEqual([])
    })

    it('正在加载时不再重复加载', async () => {
      const store = useModelsStore()
      store.isLoading = true
      vi.mocked(modelsApi.getModels).mockResolvedValue([])

      await store.loadModels()

      expect(modelsApi.getModels).not.toHaveBeenCalled()
    })
  })

  describe('loadActiveModel', () => {
    it('成功加载活跃模型', async () => {
      const store = useModelsStore()
      vi.mocked(modelsApi.getActiveModel).mockResolvedValue(mockModel)

      await store.loadActiveModel()

      expect(modelsApi.getActiveModel).toHaveBeenCalledWith('test-account-id')
      expect(store.activeModel).toEqual(mockModel)
    })

    it('加载失败时不修改活跃模型', async () => {
      const store = useModelsStore()
      store.activeModel = mockModel
      vi.mocked(modelsApi.getActiveModel).mockRejectedValue(new Error('API Error'))

      await store.loadActiveModel()

      expect(store.activeModel).toEqual(mockModel)
    })
  })

  describe('createModel', () => {
    it('成功创建模型并重新加载列表', async () => {
      const store = useModelsStore()
      const newModelConfig = { ...mockModel, id: undefined } as any
      const newModel = { ...mockModel, id: 'new-model' }
      vi.mocked(modelsApi.createModel).mockResolvedValue(newModel)
      vi.mocked(modelsApi.getModels).mockResolvedValue([newModel])

      const result = await store.createModel(newModelConfig)

      expect(modelsApi.createModel).toHaveBeenCalledWith('test-account-id', newModelConfig)
      expect(modelsApi.getModels).toHaveBeenCalled()
      expect(result).toEqual(newModel)
    })

    it('静默模式创建模型直接添加到列表', async () => {
      const store = useModelsStore()
      const newModelConfig = { ...mockModel, id: undefined } as any
      const newModel = { ...mockModel, id: 'new-model' }
      vi.mocked(modelsApi.createModel).mockResolvedValue(newModel)

      const result = await store.createModel(newModelConfig, true)

      expect(modelsApi.createModel).toHaveBeenCalled()
      expect(modelsApi.getModels).not.toHaveBeenCalled()
      expect(store.models[0]).toEqual(newModel)
      expect(result).toEqual(newModel)
    })

    it('createModelSilent 调用 createModel 并设置 silent 为 true', async () => {
      const store = useModelsStore()
      const newModelConfig = { ...mockModel, id: undefined } as any
      const newModel = { ...mockModel, id: 'new-model' }
      vi.mocked(modelsApi.createModel).mockResolvedValue(newModel)

      const result = await store.createModelSilent(newModelConfig)

      expect(modelsApi.createModel).toHaveBeenCalled()
      expect(store.models[0]).toEqual(newModel)
      expect(result).toEqual(newModel)
    })
  })

  describe('updateModel', () => {
    it('成功更新模型并重新加载列表', async () => {
      const store = useModelsStore()
      const updatedModel = { ...mockModel, name: 'Updated Model' }
      vi.mocked(modelsApi.updateModel).mockResolvedValue(updatedModel)
      vi.mocked(modelsApi.getModels).mockResolvedValue([updatedModel])

      await store.updateModel(mockModel.id, { name: 'Updated Model' })

      expect(modelsApi.updateModel).toHaveBeenCalledWith('test-account-id', mockModel.id, {
        name: 'Updated Model',
      })
      expect(modelsApi.getModels).toHaveBeenCalled()
    })

    it('静默模式更新模型直接更新列表', async () => {
      const store = useModelsStore()
      store.models = [mockModel]
      const updatedModel = { ...mockModel, name: 'Updated Model' }
      vi.mocked(modelsApi.updateModel).mockResolvedValue(updatedModel)

      const result = await store.updateModel(mockModel.id, { name: 'Updated Model' }, true)

      expect(modelsApi.updateModel).toHaveBeenCalled()
      expect(modelsApi.getModels).not.toHaveBeenCalled()
      expect(store.models[0].name).toBe('Updated Model')
      expect(result).toEqual(updatedModel)
    })

    it('updateModelSilent 调用 updateModel 并设置 silent 为 true', async () => {
      const store = useModelsStore()
      store.models = [mockModel]
      const updatedModel = { ...mockModel, name: 'Updated Model' }
      vi.mocked(modelsApi.updateModel).mockResolvedValue(updatedModel)

      const result = await store.updateModelSilent(mockModel.id, { name: 'Updated Model' })

      expect(store.models[0].name).toBe('Updated Model')
      expect(result).toEqual(updatedModel)
    })
  })

  describe('deleteModel', () => {
    it('成功删除模型并重新加载列表', async () => {
      const store = useModelsStore()
      vi.mocked(modelsApi.deleteModel).mockResolvedValue(undefined)
      vi.mocked(modelsApi.getModels).mockResolvedValue([])

      await store.deleteModel(mockModel.id)

      expect(modelsApi.deleteModel).toHaveBeenCalledWith('test-account-id', mockModel.id)
      expect(modelsApi.getModels).toHaveBeenCalled()
    })

    it('静默模式删除模型直接从列表移除', async () => {
      const store = useModelsStore()
      store.models = [mockModel]
      vi.mocked(modelsApi.deleteModel).mockResolvedValue(undefined)

      await store.deleteModel(mockModel.id, true)

      expect(modelsApi.deleteModel).toHaveBeenCalled()
      expect(modelsApi.getModels).not.toHaveBeenCalled()
      expect(store.models).toEqual([])
    })

    it('deleteModelSilent 调用 deleteModel 并设置 silent 为 true', async () => {
      const store = useModelsStore()
      store.models = [mockModel]
      vi.mocked(modelsApi.deleteModel).mockResolvedValue(undefined)

      await store.deleteModelSilent(mockModel.id)

      expect(store.models).toEqual([])
    })
  })

  describe('enableModel 和 disableModel', () => {
    it('成功启用模型', async () => {
      const store = useModelsStore()
      const disabledModel = { ...mockModel, isEnabled: false }
      store.models = [disabledModel]
      vi.mocked(modelsApi.enableModel).mockResolvedValue({ success: true, message: 'Enabled' })

      const result = await store.enableModel(disabledModel.id)

      expect(modelsApi.enableModel).toHaveBeenCalledWith('test-account-id', disabledModel.id)
      expect(store.models[0].isEnabled).toBe(true)
      expect(result).toEqual({ success: true, message: 'Enabled' })
    })

    it('成功禁用模型', async () => {
      const store = useModelsStore()
      store.models = [mockModel]
      store.activeModel = mockModel
      vi.mocked(modelsApi.disableModel).mockResolvedValue({ success: true, message: 'Disabled' })

      const result = await store.disableModel(mockModel.id)

      expect(modelsApi.disableModel).toHaveBeenCalledWith('test-account-id', mockModel.id)
      expect(store.models[0].isEnabled).toBe(false)
      expect(store.activeModel).toBeNull()
      expect(result).toEqual({ success: true, message: 'Disabled' })
    })

    it('操作失败时不更新模型状态', async () => {
      const store = useModelsStore()
      store.models = [mockModel]
      vi.mocked(modelsApi.disableModel).mockResolvedValue({ success: false, message: 'Failed' })

      const result = await store.disableModel(mockModel.id)

      expect(store.models[0].isEnabled).toBe(true)
      expect(result).toEqual({ success: false, message: 'Failed' })
    })
  })

  describe('switchModel', () => {
    it('成功切换到已启用的模型', async () => {
      const store = useModelsStore()
      store.models = [mockModel]
      vi.mocked(modelsApi.setActiveModel).mockResolvedValue({ success: true, message: '' } as any)

      const result = await store.switchModel(mockModel.id)

      expect(modelsApi.setActiveModel).toHaveBeenCalledWith('test-account-id', mockModel.id)
      expect(store.activeModel).toEqual(mockModel)
      expect(result).toBe(true)
    })

    it('模型不存在时切换失败', async () => {
      const store = useModelsStore()
      const result = await store.switchModel('non-existent-id')
      expect(result).toBe(false)
    })

    it('模型未启用时切换失败', async () => {
      const store = useModelsStore()
      const disabledModel = { ...mockModel, isEnabled: false }
      store.models = [disabledModel]
      const result = await store.switchModel(disabledModel.id)
      expect(result).toBe(false)
    })

    it('API 调用失败时抛出错误', async () => {
      const store = useModelsStore()
      store.models = [mockModel]
      vi.mocked(modelsApi.setActiveModel).mockRejectedValue(new Error('API Error'))

      await expect(store.switchModel(mockModel.id)).rejects.toThrow('API Error')
    })
  })

  describe('testModelById', () => {
    it('成功测试模型并更新测试结果', async () => {
      const store = useModelsStore()
      vi.mocked(modelsApi.testModelById).mockResolvedValue(mockTestResponse)
      vi.mocked(modelsApi.getModels).mockResolvedValue([mockModel])

      const result = await store.testModelById(mockModel.id)

      expect(store.isTesting).toBe(false)
      expect(store.testResult).toEqual(mockTestResponse)
      expect(modelsApi.testModelById).toHaveBeenCalledWith('test-account-id', mockModel.id, true)
      expect(modelsApi.getModels).toHaveBeenCalled()
      expect(result).toEqual(mockTestResponse)
    })

    it('测试期间设置 isTesting 为 true', async () => {
      const store = useModelsStore()
      let isTestingDuringCall: boolean | null = null
      vi.mocked(modelsApi.testModelById).mockImplementation(async () => {
        isTestingDuringCall = store.isTesting
        return mockTestResponse
      })

      await store.testModelById(mockModel.id)

      expect(isTestingDuringCall).toBe(true)
    })

    it('测试失败时抛出错误并重置状态', async () => {
      const store = useModelsStore()
      vi.mocked(modelsApi.testModelById).mockRejectedValue(new Error('Test failed'))

      await expect(store.testModelById(mockModel.id)).rejects.toThrow('Test failed')
      expect(store.isTesting).toBe(false)
    })

    it('测试前清空 testResult', async () => {
      const store = useModelsStore()
      store.testResult = mockTestResponse
      vi.mocked(modelsApi.testModelById).mockResolvedValue(mockTestResponse)

      await store.testModelById(mockModel.id)

      expect(store.testResult).toEqual(mockTestResponse)
    })
  })
})
