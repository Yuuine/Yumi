/**
 * 应用常量配置
 */

/** 模型选项类型 */
export interface ModelOption {
  label: string
  value: string
}

/** 提供商配置类型 */
export interface ProviderConfig {
  baseUrl: string
  models: ModelOption[]
  apiKeyUrl: string
}

/** API 提供商配置（按提供商ID索引） */
export const API_PROVIDERS: Record<string, ProviderConfig> = {
  openai: {
    baseUrl: 'https://api.openai.com/v1',
    models: [
      { label: 'GPT-4o', value: 'gpt-4o' },
      { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
      { label: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
      { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
    ],
    apiKeyUrl: 'https://platform.openai.com/api-keys',
  },
  deepseek: {
    baseUrl: 'https://api.deepseek.com',
    models: [
      { label: 'DeepSeek Chat', value: 'deepseek-chat' },
      { label: 'DeepSeek Reasoner', value: 'deepseek-reasoner' },
    ],
    apiKeyUrl: 'https://platform.deepseek.com/api_keys',
  },
  anthropic: {
    baseUrl: 'https://api.anthropic.com/v1',
    models: [
      { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
      { label: 'Claude 3 Opus', value: 'claude-3-opus-20240229' },
      { label: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' },
    ],
    apiKeyUrl: 'https://console.anthropic.com/settings/keys',
  },
  custom: {
    baseUrl: '',
    models: [{ label: '自定义模型', value: 'custom' }],
    apiKeyUrl: '',
  },
}

/** 颜色常量 */
export const COLORS = {
  PRIMARY: '#3b82f6',
  SECONDARY: '#ff9500',
  SUCCESS: '#10b981',
  WARNING: '#ff9500',
  DANGER: '#ef4444',
  TEXT_PRIMARY: '#333333',
  TEXT_SECONDARY: '#666666',
  TEXT_PLACEHOLDER: '#9ca3af',
  BORDER: '#d1d5db',
  BORDER_LIGHT: '#e5e7eb',
  BACKGROUND: '#f9fafb',
  BACKGROUND_HOVER: '#f3f4f6',
} as const

/** 尺寸常量 */
export const SIZES = {
  INPUT_HEIGHT: 40,
  BORDER_RADIUS: 6,
  ICON_SMALL: 14,
  ICON_MEDIUM: 16,
  ICON_LARGE: 20,
  SPACING_XS: 4,
  SPACING_SM: 8,
  SPACING_MD: 12,
  SPACING_LG: 16,
  SPACING_XL: 24,
} as const

/** 动画时长常量 */
export const ANIMATION_DURATION = {
  FAST: 0.15,
  NORMAL: 0.2,
  SLOW: 0.25,
} as const

/** 模型标签类型 */
export const MODEL_TAG_TYPES = {
  MODEL: 'model',
  TOOL: 'tool',
  REASONING: 'reasoning',
  DISABLED: 'disabled',
} as const
