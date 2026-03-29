import { describe, it, expect } from 'vitest'
import {
  API_PROVIDERS,
  PROVIDER_NAMES,
  PROVIDER_OPTIONS,
  MODEL_CAPABILITIES,
  getModelCapabilities,
  supportsDeepThinking,
  ANIMATION_DURATION,
  MODAL_SIZES,
  TOAST_DURATION,
  DATE_FORMATS,
  STORAGE_KEYS,
  API_ENDPOINTS,
} from '@/constants'

describe('constants - 常量模块', () => {
  describe('API_PROVIDERS', () => {
    it('包含所有预期的提供商配置', () => {
      expect(API_PROVIDERS).toHaveProperty('deepseek')
      expect(API_PROVIDERS).toHaveProperty('kimi')
      expect(API_PROVIDERS).toHaveProperty('openai')
    })

    it('每个提供商配置包含正确的结构', () => {
      Object.values(API_PROVIDERS).forEach(provider => {
        expect(provider).toHaveProperty('baseUrl')
        expect(provider).toHaveProperty('models')
        expect(provider).toHaveProperty('apiKeyUrl')
        expect(Array.isArray(provider.models)).toBe(true)
      })
    })

    it('deepseek 配置正确', () => {
      const deepseek = API_PROVIDERS.deepseek
      expect(deepseek.baseUrl).toBe('https://api.deepseek.com')
      expect(deepseek.apiKeyUrl).toBe('https://platform.deepseek.com/api_keys')
      expect(deepseek.models.length).toBe(2)
      expect(deepseek.models[0].value).toBe('deepseek-chat')
      expect(deepseek.models[1].value).toBe('deepseek-reasoner')
    })

    it('kimi 配置正确', () => {
      const kimi = API_PROVIDERS.kimi
      expect(kimi.baseUrl).toBe('https://api.moonshot.cn/v1')
      expect(kimi.apiKeyUrl).toBe('https://platform.moonshot.cn/console/api-keys')
      expect(kimi.models.length).toBe(2)
    })

    it('openai 配置正确', () => {
      const openai = API_PROVIDERS.openai
      expect(openai.baseUrl).toBe('https://api.openai.com')
      expect(openai.apiKeyUrl).toBe('https://platform.openai.com/api-keys')
      expect(openai.models.length).toBe(1)
      expect(openai.models[0].value).toBe('gpt-5.4')
    })
  })

  describe('PROVIDER_NAMES', () => {
    it('包含所有提供商的显示名称', () => {
      expect(PROVIDER_NAMES.deepseek).toBe('DeepSeek')
      expect(PROVIDER_NAMES.kimi).toBe('Kimi')
      expect(PROVIDER_NAMES.openai).toBe('OpenAI')
    })

    it('与 API_PROVIDERS 的键一致', () => {
      const providerKeys = Object.keys(API_PROVIDERS)
      const nameKeys = Object.keys(PROVIDER_NAMES)
      expect(nameKeys).toEqual(providerKeys)
    })
  })

  describe('PROVIDER_OPTIONS', () => {
    it('生成正确的选项列表', () => {
      expect(Array.isArray(PROVIDER_OPTIONS)).toBe(true)
      expect(PROVIDER_OPTIONS.length).toBe(3)

      PROVIDER_OPTIONS.forEach(option => {
        expect(option).toHaveProperty('value')
        expect(option).toHaveProperty('label')
      })
    })

    it('包含所有提供商', () => {
      const values = PROVIDER_OPTIONS.map(o => o.value)
      expect(values).toContain('deepseek')
      expect(values).toContain('kimi')
      expect(values).toContain('openai')
    })
  })

  describe('MODEL_CAPABILITIES', () => {
    it('包含预期的模型能力配置', () => {
      expect(MODEL_CAPABILITIES).toHaveProperty('deepseek-chat')
      expect(MODEL_CAPABILITIES).toHaveProperty('deepseek-reasoner')
      expect(MODEL_CAPABILITIES).toHaveProperty('kimi-k2-turbo-preview')
      expect(MODEL_CAPABILITIES).toHaveProperty('kimi-k2.5')
      expect(MODEL_CAPABILITIES).toHaveProperty('gpt-5.4')
    })

    it('每个模型能力配置包含正确的字段', () => {
      Object.values(MODEL_CAPABILITIES).forEach(capabilities => {
        expect(capabilities).toHaveProperty('toolCall')
        expect(capabilities).toHaveProperty('reasoning')
        expect(capabilities).toHaveProperty('webSearch')
        expect(capabilities).toHaveProperty('multimodal')
      })
    })

    it('deepseek-chat 能力配置正确', () => {
      const caps = MODEL_CAPABILITIES['deepseek-chat']
      expect(caps.toolCall).toBe(true)
      expect(caps.reasoning).toBe(false)
      expect(caps.webSearch).toBe(false)
      expect(caps.multimodal).toBe(false)
    })

    it('deepseek-reasoner 能力配置正确', () => {
      const caps = MODEL_CAPABILITIES['deepseek-reasoner']
      expect(caps.toolCall).toBe(true)
      expect(caps.reasoning).toBe(true)
      expect(caps.webSearch).toBe(false)
      expect(caps.multimodal).toBe(false)
    })

    it('kimi-k2.5 能力配置正确', () => {
      const caps = MODEL_CAPABILITIES['kimi-k2.5']
      expect(caps.toolCall).toBe(true)
      expect(caps.reasoning).toBe(true)
      expect(caps.webSearch).toBe(true)
      expect(caps.multimodal).toBe(true)
    })

    it('gpt-5.4 能力配置正确', () => {
      const caps = MODEL_CAPABILITIES['gpt-5.4']
      expect(caps.toolCall).toBe(true)
      expect(caps.reasoning).toBe(true)
      expect(caps.webSearch).toBe(true)
      expect(caps.multimodal).toBe(true)
    })
  })

  describe('getModelCapabilities', () => {
    it('返回已存在模型的能力配置', () => {
      const caps = getModelCapabilities('deepseek-chat')
      expect(caps).toEqual(MODEL_CAPABILITIES['deepseek-chat'])
    })

    it('不区分大小写查找模型', () => {
      const caps1 = getModelCapabilities('DEEPSEEK-CHAT')
      const caps2 = getModelCapabilities('DeepSeek-Chat')
      expect(caps1).toEqual(MODEL_CAPABILITIES['deepseek-chat'])
      expect(caps2).toEqual(MODEL_CAPABILITIES['deepseek-chat'])
    })

    it('为未知模型返回默认能力配置', () => {
      const caps = getModelCapabilities('unknown-model')
      expect(caps.toolCall).toBe(false)
      expect(caps.reasoning).toBe(false)
      expect(caps.webSearch).toBe(false)
      expect(caps.multimodal).toBe(false)
    })

    it('为空字符串返回默认配置', () => {
      expect(getModelCapabilities('')).toEqual({
        toolCall: false,
        reasoning: false,
        webSearch: false,
        multimodal: false,
      })
    })
  })

  describe('supportsDeepThinking', () => {
    it('为 kimi-k2.5 返回 true', () => {
      expect(supportsDeepThinking('kimi', 'kimi-k2.5')).toBe(true)
    })

    it('为 gpt-5.4 返回 true', () => {
      expect(supportsDeepThinking('openai', 'gpt-5.4')).toBe(true)
    })

    it('为 deepseek-reasoner 返回 false（自带推理）', () => {
      expect(supportsDeepThinking('deepseek', 'deepseek-reasoner')).toBe(false)
    })

    it('为其他模型返回 false', () => {
      expect(supportsDeepThinking('deepseek', 'deepseek-chat')).toBe(false)
      expect(supportsDeepThinking('kimi', 'kimi-k2-turbo-preview')).toBe(false)
    })

    it('不区分大小写判断模型', () => {
      expect(supportsDeepThinking('kimi', 'KIMI-K2.5')).toBe(true)
      expect(supportsDeepThinking('deepseek', 'DEEPSEEK-REASONER')).toBe(false)
    })

    it('处理未定义的模型名', () => {
      expect(supportsDeepThinking('deepseek')).toBe(false)
      expect(supportsDeepThinking('deepseek', undefined)).toBe(false)
    })
  })

  describe('其他常量配置', () => {
    describe('ANIMATION_DURATION', () => {
      it('包含正确的动画时长', () => {
        expect(ANIMATION_DURATION.FAST).toBe(150)
        expect(ANIMATION_DURATION.NORMAL).toBe(200)
        expect(ANIMATION_DURATION.SLOW).toBe(300)
      })
    })

    describe('MODAL_SIZES', () => {
      it('包含正确的模态框尺寸', () => {
        expect(MODAL_SIZES.SMALL).toBe('small')
        expect(MODAL_SIZES.MEDIUM).toBe('medium')
        expect(MODAL_SIZES.LARGE).toBe('large')
        expect(MODAL_SIZES.XLARGE).toBe('xlarge')
      })
    })

    describe('TOAST_DURATION', () => {
      it('包含正确的 Toast 时长', () => {
        expect(TOAST_DURATION.SHORT).toBe(2000)
        expect(TOAST_DURATION.NORMAL).toBe(2500)
        expect(TOAST_DURATION.LONG).toBe(5000)
      })
    })

    describe('DATE_FORMATS', () => {
      it('包含正确的日期格式', () => {
        expect(DATE_FORMATS.SHORT).toBe('YYYY-MM-DD')
        expect(DATE_FORMATS.LONG).toBe('YYYY年MM月DD日')
        expect(DATE_FORMATS.DATETIME).toBe('YYYY-MM-DD HH:mm:ss')
        expect(DATE_FORMATS.RELATIVE).toBe('relative')
      })
    })

    describe('STORAGE_KEYS', () => {
      it('包含正确的存储键', () => {
        expect(STORAGE_KEYS.ACCOUNT).toBe('yumi_account')
        expect(STORAGE_KEYS.SETTINGS).toBe('yumi_settings')
        expect(STORAGE_KEYS.THEME).toBe('yumi_theme')
      })
    })

    describe('API_ENDPOINTS', () => {
      it('包含正确的 API 端点', () => {
        expect(API_ENDPOINTS.CHAT).toBe('/chat')
        expect(API_ENDPOINTS.CHAT_HISTORY).toBe('/chat/history')
        expect(API_ENDPOINTS.USER).toBe('/user')
        expect(API_ENDPOINTS.CONVERSATIONS).toBe('/conversations')
        expect(API_ENDPOINTS.CHARACTER_CARDS).toBe('/character-cards')
        expect(API_ENDPOINTS.MODELS).toBe('/models')
      })
    })
  })
})
