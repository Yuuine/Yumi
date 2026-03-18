import type { ModelConfig, ModelTestRequest, ModelTestResponse, ModelType, TestStatus } from '@/types'
import { httpClient } from './http-client'

export const modelsApi = {
  async getModels(): Promise<ModelConfig[]> {
    const data = await httpClient.get<Record<string, unknown>[]>('/models')
    return data.map(item => transformToModelConfig(item))
  },

  async createModel(config: Omit<ModelConfig, 'id'>): Promise<ModelConfig> {
    const result = await httpClient.post<Record<string, unknown>>(
      '/models',
      transformToApiFormat(config)
    )
    return transformToModelConfig(result)
  },

  async updateModel(modelId: string, config: Partial<ModelConfig>): Promise<ModelConfig> {
    const result = await httpClient.put<Record<string, unknown>>(
      `/models/${modelId}`,
      transformToApiFormat(config)
    )
    return transformToModelConfig(result)
  },

  async deleteModel(modelId: string): Promise<void> {
    await httpClient.delete(`/models/${modelId}`)
  },

  async enableModel(modelId: string): Promise<{ success: boolean; message: string }> {
    return httpClient.post(`/models/${modelId}/enable`)
  },

  async disableModel(modelId: string): Promise<{ success: boolean; message: string }> {
    return httpClient.post(`/models/${modelId}/disable`)
  },

  async testModel(request: ModelTestRequest): Promise<ModelTestResponse> {
    return httpClient.post<ModelTestResponse>('/test', {
      baseUrl: request.baseUrl,
      apiKey: request.apiKey,
      modelName: request.modelName,
      testMessage: request.testMessage,
    })
  },

  async testModelById(
    modelId: string
  ): Promise<{ success: boolean; message: string; latency?: number }> {
    return httpClient.post(`/models/${modelId}/test`)
  },

  async getActiveModel(): Promise<ModelConfig | null> {
    const data = await httpClient.get<Record<string, unknown> | null>('/active')
    return data ? transformToModelConfig(data) : null
  },
}

function transformToModelConfig(data: Record<string, unknown>): ModelConfig {
  return {
    id: data.id as string,
    providerId: (data.providerId || data.provider_id) as string,
    name: data.name as string,
    baseUrl: (data.baseUrl || data.base_url) as string,
    apiKey: (data.apiKey || data.api_key || '') as string,
    modelName: (data.modelName || data.model_name) as string,
    customModelName: (data.customModelName || data.custom_model_name) as string | undefined,
    modelType: (data.modelType || data.model_type || 'text') as ModelType,
    maxTokens: (data.maxTokens || data.max_tokens || 4096) as number,
    temperature: (data.temperature ?? 0.85) as number,
    isEnabled: (data.isEnabled ?? data.is_enabled ?? false) as boolean,
    isTested: (data.isTested ?? data.is_tested ?? false) as boolean,
    testStatus: (data.testStatus || data.test_status || 'untested') as TestStatus,
    lastTestAt: (data.lastTestAt || data.last_test_at) as string | undefined,
    lastTestMessage: (data.lastTestMessage || data.last_test_message) as string | undefined,
    editCount: (data.editCount ?? data.edit_count ?? 0) as number,
    createdAt: (data.createdAt || data.created_at) as string | undefined,
    updatedAt: (data.updatedAt || data.updated_at) as string | undefined,
  }
}

function transformToApiFormat(config: Partial<ModelConfig>): Record<string, unknown> {
  const result: Record<string, unknown> = {}

  if (config.providerId !== undefined) result.providerId = config.providerId
  if (config.name !== undefined) result.name = config.name
  if (config.baseUrl !== undefined) result.baseUrl = config.baseUrl
  if (config.apiKey !== undefined) result.apiKey = config.apiKey
  if (config.modelName !== undefined) result.modelName = config.modelName
  if (config.customModelName !== undefined) result.customModelName = config.customModelName
  if (config.modelType !== undefined) result.modelType = config.modelType
  if (config.maxTokens !== undefined) result.maxTokens = config.maxTokens
  if (config.temperature !== undefined) result.temperature = config.temperature
  if (config.isEnabled !== undefined) result.isEnabled = config.isEnabled
  if (config.isTested !== undefined) result.isTested = config.isTested
  if (config.testStatus !== undefined) result.testStatus = config.testStatus
  if (config.lastTestAt !== undefined) result.lastTestAt = config.lastTestAt
  if (config.lastTestMessage !== undefined) result.lastTestMessage = config.lastTestMessage
  if (config.editCount !== undefined) result.editCount = config.editCount
  if ((config as { apiKeyUnchanged?: boolean }).apiKeyUnchanged !== undefined) {
    result.apiKeyUnchanged = (config as { apiKeyUnchanged?: boolean }).apiKeyUnchanged
  }

  return result
}
