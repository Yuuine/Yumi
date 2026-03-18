import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ModelConfig, ModelTestRequest, ModelTestResponse } from '@/types'
import { modelsApi } from '@/api/models'
import { logger } from '@/utils/logger'

/**
 * 模型管理 Store
 * 负责管理 AI 模型配置、切换和测试
 */
export const useModelsStore = defineStore('models', () => {
  const models = ref<ModelConfig[]>([])
  const activeModel = ref<ModelConfig | null>(null)
  const isLoading = ref(false)
  const isTesting = ref(false)
  const testResult = ref<ModelTestResponse | null>(null)

  /**
   * 在模型列表中查找模型索引
   */
  function findModelIndex(modelId: string): number {
    return models.value.findIndex(m => m.id === modelId)
  }

  /**
   * 更新模型列表中的模型状态
   */
  function updateModelInList(modelId: string, updates: Partial<ModelConfig>): boolean {
    const index = findModelIndex(modelId)
    if (index !== -1) {
      models.value[index] = { ...models.value[index], ...updates }
      return true
    }
    return false
  }

  /**
   * 加载所有模型配置
   */
  async function loadModels(): Promise<void> {
    if (isLoading.value) return

    isLoading.value = true
    try {
      models.value = await modelsApi.getModels()
    } catch (error) {
      logger.error('ModelsStore', 'Failed to load models', error)
      models.value = []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 加载当前活动的模型
   */
  async function loadActiveModel(): Promise<void> {
    try {
      activeModel.value = await modelsApi.getActiveModel()
    } catch (error) {
      logger.error('ModelsStore', 'Failed to load active model', error)
    }
  }

  /**
   * 创建新模型配置
   */
  async function createModel(config: Omit<ModelConfig, 'id'>): Promise<ModelConfig> {
    isLoading.value = true
    try {
      const newModel = await modelsApi.createModel(config)
      await loadModels()
      return newModel
    } catch (error) {
      logger.error('ModelsStore', 'Failed to create model', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 静默创建模型（不触发全局加载状态）
   */
  async function createModelSilent(config: Omit<ModelConfig, 'id'>): Promise<ModelConfig> {
    try {
      const newModel = await modelsApi.createModel(config)
      models.value.unshift(newModel)
      return newModel
    } catch (error) {
      logger.error('ModelsStore', 'Failed to create model', error)
      throw error
    }
  }

  /**
   * 更新模型配置
   */
  async function updateModel(modelId: string, config: Partial<ModelConfig>): Promise<void> {
    isLoading.value = true
    try {
      await modelsApi.updateModel(modelId, config)
      await loadModels()
    } catch (error) {
      logger.error('ModelsStore', 'Failed to update model', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 静默更新模型（不触发全局加载状态）
   */
  async function updateModelSilent(
    modelId: string,
    config: Partial<ModelConfig>
  ): Promise<ModelConfig> {
    try {
      const updatedModel = await modelsApi.updateModel(modelId, config)
      updateModelInList(modelId, updatedModel)
      return updatedModel
    } catch (error) {
      logger.error('ModelsStore', 'Failed to update model', error)
      throw error
    }
  }

  /**
   * 删除模型配置
   */
  async function deleteModel(modelId: string): Promise<void> {
    isLoading.value = true
    try {
      await modelsApi.deleteModel(modelId)
      await loadModels()
    } catch (error) {
      logger.error('ModelsStore', 'Failed to delete model', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 静默删除模型（不触发全局加载状态）
   */
  async function deleteModelSilent(modelId: string): Promise<void> {
    try {
      await modelsApi.deleteModel(modelId)
      const index = findModelIndex(modelId)
      if (index !== -1) {
        models.value.splice(index, 1)
      }
    } catch (error) {
      logger.error('ModelsStore', 'Failed to delete model', error)
      throw error
    }
  }

  /**
   * 启用模型
   */
  async function enableModel(modelId: string): Promise<{ success: boolean; message: string }> {
    try {
      const result = await modelsApi.enableModel(modelId)
      if (result.success) {
        updateModelInList(modelId, { isEnabled: true })
      }
      return result
    } catch (error) {
      logger.error('ModelsStore', 'Failed to enable model', error)
      throw error
    }
  }

  /**
   * 禁用模型
   */
  async function disableModel(modelId: string): Promise<{ success: boolean; message: string }> {
    try {
      const result = await modelsApi.disableModel(modelId)
      if (result.success) {
        updateModelInList(modelId, { isEnabled: false })
        if (activeModel.value?.id === modelId) {
          activeModel.value = null
        }
      }
      return result
    } catch (error) {
      logger.error('ModelsStore', 'Failed to disable model', error)
      throw error
    }
  }

  /**
   * 测试模型连接
   */
  async function testModel(request: ModelTestRequest): Promise<ModelTestResponse> {
    isTesting.value = true
    testResult.value = null
    try {
      testResult.value = await modelsApi.testModel(request)
      return testResult.value
    } catch (error) {
      logger.error('ModelsStore', 'Failed to test model', error)
      throw error
    } finally {
      isTesting.value = false
    }
  }

  /**
   * 通过模型ID测试连接
   */
  async function testModelById(modelId: string): Promise<ModelTestResponse> {
    isTesting.value = true
    testResult.value = null
    try {
      const result = await modelsApi.testModelById(modelId)
      testResult.value = {
        success: result.success,
        message: result.message,
        latency: result.latency,
        response: result.response,
        reasoning: result.reasoning,
      }
      await loadModels()
      return testResult.value
    } catch (error) {
      logger.error('ModelsStore', 'Failed to test model', error)
      throw error
    } finally {
      isTesting.value = false
    }
  }

  /**
   * 切换活动模型
   * 仅设置当前活动模型，不影响其他模型的启用状态
   */
  async function switchModel(modelId: string): Promise<boolean> {
    const model = models.value.find(m => m.id === modelId)
    if (!model) {
      logger.error('ModelsStore', 'Model not found', { modelId })
      return false
    }

    if (!model.isEnabled) {
      logger.error('ModelsStore', 'Model is not enabled', { modelId })
      return false
    }

    try {
      const result = await modelsApi.setActiveModel(modelId)
      if (result.success) {
        activeModel.value = model
        logger.info('ModelsStore', 'Model switched', { modelName: model.name })
        return true
      }
      return false
    } catch (error) {
      logger.error('ModelsStore', 'Failed to switch model', error)
      throw error
    }
  }

  /**
   * 已启用且有 API Key 的模型列表
   */
  const enabledModels = computed(() => models.value.filter(m => m.isEnabled && m.apiKey))

  return {
    models,
    activeModel,
    enabledModels,
    isLoading,
    isTesting,
    testResult,
    loadModels,
    loadActiveModel,
    createModel,
    createModelSilent,
    updateModel,
    updateModelSilent,
    deleteModel,
    deleteModelSilent,
    enableModel,
    disableModel,
    testModel,
    testModelById,
    switchModel,
  }
})
