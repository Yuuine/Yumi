/**
 * 应用常量配置
 */

/** 模型选项类型 */
export interface ModelOption {
  label: string
  value: string
  modelType?: 'text' | 'image'
}

/** 提供商配置类型 */
export interface ProviderConfig {
  baseUrl: string
  models: ModelOption[]
  apiKeyUrl: string
}

/** API 提供商配置（按提供商ID索引） */
export const API_PROVIDERS: Record<string, ProviderConfig> = {
  deepseek: {
    baseUrl: 'https://api.deepseek.com',
    models: [
      { label: 'DeepSeek Chat', value: 'deepseek-chat' },
      { label: 'DeepSeek Reasoner', value: 'deepseek-reasoner' },
    ],
    apiKeyUrl: 'https://platform.deepseek.com/api_keys',
  },
  kimi: {
    baseUrl: 'https://api.moonshot.cn/v1',
    models: [
      { label: 'Kimi K2.5', value: 'kimi-k2.5' },
      { label: 'Kimi K2 Turbo Preview', value: 'kimi-k2-turbo-preview' },
    ],
    apiKeyUrl: 'https://platform.moonshot.cn/console/api-keys',
  },
  openai: {
    baseUrl: 'https://api.openai.com',
    models: [{ label: 'GPT-5.4', value: 'gpt-5.4' }],
    apiKeyUrl: 'https://platform.openai.com/api-keys',
  },
}

/** 提供商显示名称映射 */
export const PROVIDER_NAMES: Record<string, string> = {
  deepseek: 'DeepSeek',
  kimi: 'Kimi',
  openai: 'OpenAI',
}

/** 提供商选项列表（用于下拉选择） */
export const PROVIDER_OPTIONS = Object.entries(PROVIDER_NAMES).map(([value, label]) => ({
  value,
  label,
}))

/** 模型能力配置 */
export interface ModelCapabilities {
  toolCall: boolean
  reasoning: boolean
  webSearch: boolean
  multimodal: boolean
}

export const MODEL_CAPABILITIES: Record<string, ModelCapabilities> = {
  'deepseek-chat': {
    toolCall: true,
    reasoning: false,
    webSearch: false,
    multimodal: false,
  },
  'deepseek-reasoner': {
    toolCall: true,
    reasoning: true,
    webSearch: false,
    multimodal: false,
  },
  'kimi-k2-turbo-preview': {
    toolCall: true,
    reasoning: false,
    webSearch: true,
    multimodal: false,
  },
  'kimi-k2.5': {
    toolCall: true,
    reasoning: true,
    webSearch: true,
    multimodal: true,
  },
  'gpt-5.4': {
    toolCall: true,
    reasoning: true,
    webSearch: true,
    multimodal: true,
  },
}

export function getModelCapabilities(modelName: string): ModelCapabilities {
  return (
    MODEL_CAPABILITIES[modelName.toLowerCase()] || {
      toolCall: false,
      reasoning: false,
      webSearch: false,
      multimodal: false,
    }
  )
}

/** 支持深度思考开关的模型（通过 thinking 参数控制） */
const DEEP_THINKING_MODELS = new Set(['kimi-k2.5', 'gpt-5.4'])

/** reasoner 类模型自带推理能力，不显示深度思考按钮 */
const REASONER_MODELS = new Set(['deepseek-reasoner'])

/**
 * 判断当前模型是否支持深度思考开关
 * - deepseek-reasoner: 不支持（自带推理，按钮隐藏）
 * - deepseek-chat, kimi-k2.5: 支持
 */
export function supportsDeepThinking(_providerId: string, modelName?: string): boolean {
  const name = (modelName || '').toLowerCase()
  if (REASONER_MODELS.has(name)) return false
  return DEEP_THINKING_MODELS.has(name)
}

export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 200,
  SLOW: 300,
}

export const MODAL_SIZES = {
  SMALL: 'small',
  MEDIUM: 'medium',
  LARGE: 'large',
  XLARGE: 'xlarge',
} as const

export const TOAST_DURATION = {
  SHORT: 2000,
  NORMAL: 2500,
  LONG: 5000,
}

export const DATE_FORMATS = {
  SHORT: 'YYYY-MM-DD',
  LONG: 'YYYY年MM月DD日',
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  RELATIVE: 'relative',
}

export const STORAGE_KEYS = {
  ACCOUNT: 'yumi_account',
  SETTINGS: 'yumi_settings',
  THEME: 'yumi_theme',
}

export const API_ENDPOINTS = {
  CHAT: '/chat',
  CHAT_HISTORY: '/chat/history',
  USER: '/user',
  CONVERSATIONS: '/conversations',
  CHARACTER_CARDS: '/character-cards',
  MODELS: '/models',
}
