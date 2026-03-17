import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ModelConfig, ModelTestRequest, ModelTestResponse } from '@/types'
import { modelsApi } from '@/api/models'

export const useModelsStore = defineStore('models', () => {
  const models = ref<ModelConfig[]>([])
  const activeModel = ref<ModelConfig | null>(null)
  const isLoading = ref(false)
  const isTesting = ref(false)
  const testResult = ref<ModelTestResponse | null>(null)

  async function loadModels() {
    if (isLoading.value) return

    isLoading.value = true
    try {
      models.value = await modelsApi.getModels()
    } catch (error) {
      console.error('Failed to load models:', error)
      models.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function loadActiveModel() {
    try {
      activeModel.value = await modelsApi.getActiveModel()
    } catch (error) {
      console.error('Failed to load active model:', error)
    }
  }

  async function createModel(config: Omit<ModelConfig, 'id'>) {
    isLoading.value = true
    try {
      const newModel = await modelsApi.createModel(config)
      await loadModels()
      return newModel
    } catch (error) {
      console.error('Failed to create model:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function createModelSilent(config: Omit<ModelConfig, 'id'>) {
    try {
      const newModel = await modelsApi.createModel(config)
      models.value.unshift(newModel)
      return newModel
    } catch (error) {
      console.error('Failed to create model:', error)
      throw error
    }
  }

  async function updateModel(modelId: string, config: Partial<ModelConfig>) {
    isLoading.value = true
    try {
      await modelsApi.updateModel(modelId, config)
      await loadModels()
    } catch (error) {
      console.error('Failed to update model:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function updateModelSilent(modelId: string, config: Partial<ModelConfig>) {
    try {
      const updatedModel = await modelsApi.updateModel(modelId, config)
      const index = models.value.findIndex(m => m.id === modelId)
      if (index !== -1) {
        models.value[index] = updatedModel
      }
      return updatedModel
    } catch (error) {
      console.error('Failed to update model:', error)
      throw error
    }
  }

  async function deleteModel(modelId: string) {
    isLoading.value = true
    try {
      await modelsApi.deleteModel(modelId)
      await loadModels()
    } catch (error) {
      console.error('Failed to delete model:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function deleteModelSilent(modelId: string) {
    try {
      await modelsApi.deleteModel(modelId)
      const index = models.value.findIndex(m => m.id === modelId)
      if (index !== -1) {
        models.value.splice(index, 1)
      }
    } catch (error) {
      console.error('Failed to delete model:', error)
      throw error
    }
  }

  async function enableModel(modelId: string) {
    try {
      const result = await modelsApi.enableModel(modelId)
      if (result.success) {
        const index = models.value.findIndex(m => m.id === modelId)
        if (index !== -1) {
          models.value[index].isEnabled = true
        }
        await loadActiveModel()
      }
      return result
    } catch (error) {
      console.error('Failed to enable model:', error)
      throw error
    }
  }

  async function disableModel(modelId: string) {
    try {
      const result = await modelsApi.disableModel(modelId)
      if (result.success) {
        const index = models.value.findIndex(m => m.id === modelId)
        if (index !== -1) {
          models.value[index].isEnabled = false
        }
        await loadActiveModel()
      }
      return result
    } catch (error) {
      console.error('Failed to disable model:', error)
      throw error
    }
  }

  async function testModel(request: ModelTestRequest) {
    isTesting.value = true
    testResult.value = null
    try {
      testResult.value = await modelsApi.testModel(request)
      return testResult.value
    } catch (error) {
      console.error('Failed to test model:', error)
      throw error
    } finally {
      isTesting.value = false
    }
  }

  async function testModelById(modelId: string) {
    isTesting.value = true
    try {
      const result = await modelsApi.testModelById(modelId)
      await loadModels()
      return result
    } catch (error) {
      console.error('Failed to test model:', error)
      throw error
    } finally {
      isTesting.value = false
    }
  }

  return {
    models,
    activeModel,
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
  }
})
