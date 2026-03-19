import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ModelConfig, ModelTestResponse } from '@/types'
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
   * 在模型列表中查找模型
   */
  function findModel(modelId: string): ModelConfig | undefined {
    return models.value.find(m => m.id === modelId)
  }

  /**
   * 更新模型列表中的模型状态
   */
  function updateModelInList(modelId: string, updates: Partial<ModelConfig>): boolean {
    const index = findModelIndex(modelId)
    if (index === -1) return false

    models.value[index] = { ...models.value[index], ...updates }
    return true
  }

  /**
   * 从模型列表中移除模型
   */
  function removeModelFromList(modelId: string): boolean {
    const index = findModelIndex(modelId)
    if (index === -1) return false

    models.value.splice(index, 1)
    return true
  }

  /**
   * 通用的带加载状态的异步执行器
   * @param asyncFn - 要执行的异步函数
   * @param shouldSetLoading - 是否设置全局加载状态，默认 true
   */
  async function executeWithLoading<T>(
    asyncFn: () => Promise<T>,
    shouldSetLoading = true
  ): Promise<T> {
    if (shouldSetLoading) {
      isLoading.value = true
    }
    try {
      return await asyncFn()
    } finally {
      if (shouldSetLoading) {
        isLoading.value = false
      }
    }
  }

  /**
   * 加载所有模型配置
   */
  async function loadModels(): Promise<void> {
    if (isLoading.value) return

    await executeWithLoading(async () => {
      try {
        models.value = await modelsApi.getModels()
      } catch (error) {
        logger.error('ModelsStore', 'Failed to load models', error)
        models.value = []
      }
    })
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
   * @param config - 模型配置（不含 id）
   * @param silent - 是否静默模式（不触发全局加载状态，不重新加载列表）
   */
  async function createModel(
    config: Omit<ModelConfig, 'id'>,
    silent = false
  ): Promise<ModelConfig> {
    const newModel = await executeWithLoading(
      () => modelsApi.createModel(config),
      !silent
    )

    if (silent) {
      models.value.unshift(newModel)
    } else {
      await loadModels()
    }

    return newModel
  }

  /**
   * 静默创建模型（不触发全局加载状态）
   */
  async function createModelSilent(config: Omit<ModelConfig, 'id'>): Promise<ModelConfig> {
    return createModel(config, true)
  }

  /**
   * 更新模型配置
   * @param modelId - 模型 ID
   * @param config - 要更新的配置
   * @param silent - 是否静默模式
   */
  async function updateModel(
    modelId: string,
    config: Partial<ModelConfig>,
    silent = false
  ): Promise<ModelConfig | void> {
    const updatedModel = await executeWithLoading(
      () => modelsApi.updateModel(modelId, config),
      !silent
    )

    if (silent) {
      updateModelInList(modelId, updatedModel)
      return updatedModel
    }

    await loadModels()
  }

  /**
   * 静默更新模型（不触发全局加载状态）
   */
  async function updateModelSilent(
    modelId: string,
    config: Partial<ModelConfig>
  ): Promise<ModelConfig> {
    return updateModel(modelId, config, true) as Promise<ModelConfig>
  }

  /**
   * 删除模型配置
   * @param modelId - 模型 ID
   * @param silent - 是否静默模式
   */
  async function deleteModel(modelId: string, silent = false): Promise<void> {
    await executeWithLoading(
      () => modelsApi.deleteModel(modelId),
      !silent
    )

    if (silent) {
      removeModelFromList(modelId)
    } else {
      await loadModels()
    }
  }

  /**
   * 静默删除模型（不触发全局加载状态）
   */
  async function deleteModelSilent(modelId: string): Promise<void> {
    return deleteModel(modelId, true)
  }

  /**
   * 切换模型启用状态
   * @param modelId - 模型 ID
   * @param enabled - 是否启用
   */
  async function toggleModelEnabled(
    modelId: string,
    enabled: boolean
  ): Promise<{ success: boolean; message: string }> {
    const apiCall = enabled ? modelsApi.enableModel : modelsApi.disableModel
    const result = await apiCall(modelId)

    if (result.success) {
      updateModelInList(modelId, { isEnabled: enabled })

      if (!enabled && activeModel.value?.id === modelId) {
        activeModel.value = null
      }
    }

    return result
  }

  /**
   * 启用模型
   */
  async function enableModel(modelId: string): Promise<{ success: boolean; message: string }> {
    return toggleModelEnabled(modelId, true)
  }

  /**
   * 禁用模型
   */
  async function disableModel(modelId: string): Promise<{ success: boolean; message: string }> {
    return toggleModelEnabled(modelId, false)
  }

  /**
   * 通过模型ID测试连接
   * @param modelId - 模型 ID
   * @param verbose - 是否返回详细测试信息，默认 true
   */
  async function testModelById(modelId: string, verbose = true): Promise<ModelTestResponse> {
    isTesting.value = true
    testResult.value = null

    try {
      logger.info('ModelsStore', 'Testing model', { modelId, verbose })
      const result = await modelsApi.testModelById(modelId, verbose)

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
   * @param modelId - 目标模型 ID
   * @returns 是否切换成功
   */
  async function switchModel(modelId: string): Promise<boolean> {
    const model = findModel(modelId)

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

      if (!result.success) return false

      activeModel.value = model
      logger.info('ModelsStore', 'Model switched', { modelName: model.name })
      return true
    } catch (error) {
      logger.error('ModelsStore', 'Failed to switch model', error)
      throw error
    }
  }

  /**
   * 已启用且有 API Key 的模型列表
   */
  const enabledModels = computed(() =>
    models.value.filter(m => m.isEnabled && m.apiKey)
  )

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
    testModelById,
    switchModel,
  }
})
