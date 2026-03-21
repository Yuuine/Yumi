import type {
  ModelConfig,
  ModelTestRequest,
  ModelTestResponse,
  ModelType,
  TestStatus,
} from '@/types'
import { httpClient } from './http-client'

interface ApiModelData {
  id: string
  provider_id?: string
  providerId?: string
  name: string
  base_url?: string
  baseUrl?: string
  api_key?: string
  apiKey?: string
  model_name?: string
  modelName?: string
  custom_model_name?: string
  customModelName?: string
  model_type?: ModelType
  modelType?: ModelType
  max_tokens?: number
  maxTokens?: number
  temperature?: number
  is_enabled?: boolean
  isEnabled?: boolean
  is_tested?: boolean
  isTested?: boolean
  test_status?: TestStatus
  testStatus?: TestStatus
  last_test_at?: string
  lastTestAt?: string
  last_test_message?: string
  lastTestMessage?: string
  edit_count?: number
  editCount?: number
  created_at?: string
  createdAt?: string
  updated_at?: string
  updatedAt?: string
}

const DEFAULT_MODEL_CONFIG: Omit<
  ModelConfig,
  'id' | 'providerId' | 'name' | 'baseUrl' | 'apiKey' | 'modelName'
> = {
  modelType: 'text',
  maxTokens: 4096,
  temperature: 0.85,
  isEnabled: false,
  isTested: false,
  testStatus: 'untested',
  editCount: 0,
}

function transformToModelConfig(data: ApiModelData): ModelConfig {
  return {
    id: data.id,
    providerId: data.provider_id ?? data.providerId ?? '',
    name: data.name,
    baseUrl: data.base_url ?? data.baseUrl ?? '',
    apiKey: data.api_key ?? data.apiKey ?? '',
    modelName: data.model_name ?? data.modelName ?? '',
    customModelName: data.custom_model_name ?? data.customModelName,
    modelType: data.model_type ?? data.modelType ?? DEFAULT_MODEL_CONFIG.modelType,
    maxTokens: data.max_tokens ?? data.maxTokens ?? DEFAULT_MODEL_CONFIG.maxTokens,
    temperature: data.temperature ?? DEFAULT_MODEL_CONFIG.temperature,
    isEnabled: data.is_enabled ?? data.isEnabled ?? DEFAULT_MODEL_CONFIG.isEnabled,
    isTested: data.is_tested ?? data.isTested ?? DEFAULT_MODEL_CONFIG.isTested,
    testStatus: data.test_status ?? data.testStatus ?? DEFAULT_MODEL_CONFIG.testStatus,
    lastTestAt: data.last_test_at ?? data.lastTestAt,
    lastTestMessage: data.last_test_message ?? data.lastTestMessage,
    editCount: data.edit_count ?? data.editCount ?? DEFAULT_MODEL_CONFIG.editCount,
    createdAt: data.created_at ?? data.createdAt,
    updatedAt: data.updated_at ?? data.updatedAt,
  }
}

function transformToApiFormat(
  config: Partial<ModelConfig> & { apiKeyUnchanged?: boolean }
): Record<string, unknown> {
  const result: Record<string, unknown> = {}

  const mapping: Record<string, keyof typeof config> = {
    providerId: 'providerId',
    name: 'name',
    baseUrl: 'baseUrl',
    apiKey: 'apiKey',
    modelName: 'modelName',
    customModelName: 'customModelName',
    modelType: 'modelType',
    maxTokens: 'maxTokens',
    temperature: 'temperature',
    isEnabled: 'isEnabled',
    isTested: 'isTested',
    testStatus: 'testStatus',
    lastTestAt: 'lastTestAt',
    lastTestMessage: 'lastTestMessage',
    editCount: 'editCount',
  }

  for (const [apiKey, configKey] of Object.entries(mapping)) {
    const value = config[configKey]
    if (value !== undefined) {
      result[apiKey] = value
    }
  }

  if (config.apiKeyUnchanged !== undefined) {
    result.apiKeyUnchanged = config.apiKeyUnchanged
  }

  return result
}

export const modelsApi = {
  async getModels(accountId: string): Promise<ModelConfig[]> {
    const data = await httpClient.get<ApiModelData[]>('/models', {
      params: { accountId },
    })
    return data.map(transformToModelConfig)
  },

  async createModel(accountId: string, config: Omit<ModelConfig, 'id'>): Promise<ModelConfig> {
    const result = await httpClient.post<ApiModelData>('/models', transformToApiFormat(config), {
      params: { accountId },
    })
    return transformToModelConfig(result)
  },

  async updateModel(
    accountId: string,
    modelId: string,
    config: Partial<ModelConfig>
  ): Promise<ModelConfig> {
    const result = await httpClient.put<ApiModelData>(
      `/models/${modelId}`,
      transformToApiFormat(config),
      { params: { accountId } }
    )
    return transformToModelConfig(result)
  },

  async deleteModel(accountId: string, modelId: string): Promise<void> {
    await httpClient.delete(`/models/${modelId}`, { params: { accountId } })
  },

  async enableModel(
    accountId: string,
    modelId: string
  ): Promise<{ success: boolean; message: string }> {
    return httpClient.post(`/models/${modelId}/enable`, undefined, { params: { accountId } })
  },

  async disableModel(
    accountId: string,
    modelId: string
  ): Promise<{ success: boolean; message: string }> {
    return httpClient.post(`/models/${modelId}/disable`, undefined, { params: { accountId } })
  },

  async setActiveModel(
    accountId: string,
    modelId: string
  ): Promise<{ success: boolean; message: string }> {
    return httpClient.post(`/models/${modelId}/set_active`, undefined, { params: { accountId } })
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
    accountId: string,
    modelId: string,
    verbose = true
  ): Promise<{
    success: boolean
    message: string
    response?: string
    reasoning?: string
    latency?: number
  }> {
    return httpClient.post(`/models/${modelId}/test`, { verbose }, { params: { accountId } })
  },

  async getActiveModel(accountId: string): Promise<ModelConfig | null> {
    const data = await httpClient.get<ApiModelData | null>('/active', {
      params: { accountId },
    })
    return data ? transformToModelConfig(data) : null
  },
}
