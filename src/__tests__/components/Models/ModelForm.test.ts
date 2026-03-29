import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ModelForm from '@/components/Models/ModelForm.vue'

vi.mock('@/components/icons', () => ({
  IconChevronDown: { template: '<span data-test="icon-chevron-down"></span>' },
  IconLink: { template: '<span data-test="icon-link"></span>' },
  IconCopy: { template: '<span data-test="icon-copy"></span>' },
}))

vi.mock('@/constants', () => ({
  API_PROVIDERS: {
    deepseek: {
      baseUrl: 'https://api.deepseek.com',
      apiKeyUrl: 'https://platform.deepseek.com/settings/api_keys',
      models: [
        { value: 'deepseek-chat', label: 'deepseek-chat' },
        { value: 'deepseek-reasoner', label: 'deepseek-reasoner' },
      ],
    },
    openai: {
      baseUrl: 'https://api.openai.com/v1',
      apiKeyUrl: 'https://platform.openai.com/account/api-keys',
      models: [
        { value: 'gpt-4', label: 'GPT-4' },
        { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
      ],
    },
  },
  PROVIDER_OPTIONS: [
    { value: 'deepseek', label: 'DeepSeek' },
    { value: 'openai', label: 'OpenAI' },
  ],
}))

describe('ModelForm - 模型表单组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('可以正常渲染', () => {
      const wrapper = mount(ModelForm)
      expect(wrapper.find('.form-section').exists()).toBe(true)
    })

    it('渲染两个表单部分', () => {
      const wrapper = mount(ModelForm)
      const sections = wrapper.findAll('.form-section')
      expect(sections.length).toBe(2)
    })

    it('渲染提供商配置部分', () => {
      const wrapper = mount(ModelForm)
      expect(wrapper.text()).toContain('提供商配置')
    })

    it('渲染模型配置部分', () => {
      const wrapper = mount(ModelForm)
      expect(wrapper.text()).toContain('模型配置')
    })
  })

  describe('表单输入', () => {
    it('渲染提供商选择器', () => {
      const wrapper = mount(ModelForm)
      expect(wrapper.find('select').exists()).toBe(true)
    })

    it('渲染 API 地址输入框', () => {
      const wrapper = mount(ModelForm)
      const inputs = wrapper.findAll('input[type="text"]')
      expect(inputs.length).toBeGreaterThan(0)
    })

    it('渲染 API 密钥输入框', () => {
      const wrapper = mount(ModelForm)
      expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    })

    it('渲染显示名称输入框', () => {
      const wrapper = mount(ModelForm)
      expect(wrapper.text()).toContain('显示名称')
    })

    it('渲染模型选择器', () => {
      const wrapper = mount(ModelForm)
      const selects = wrapper.findAll('select')
      expect(selects.length).toBe(2)
    })
  })

  describe('Props', () => {
    it('接受可选的 modelValue prop', () => {
      const initialValue = {
        providerId: 'openai',
        name: 'My Model',
        baseUrl: 'https://api.test.com',
        apiKey: 'test-key',
        modelName: 'gpt-4',
      }
      const wrapper = mount(ModelForm, {
        props: {
          modelValue: initialValue,
        },
      })
      expect(wrapper.props('modelValue')).toEqual(initialValue)
    })

    it('接受可选的 isEditing prop', () => {
      const wrapper = mount(ModelForm, {
        props: {
          isEditing: true,
        },
      })
      expect(wrapper.props('isEditing')).toBe(true)
    })

    it('接受可选的 originalApiKey prop', () => {
      const wrapper = mount(ModelForm, {
        props: {
          originalApiKey: 'original-key',
        },
      })
      expect(wrapper.props('originalApiKey')).toBe('original-key')
    })
  })

  describe('Emits', () => {
    it('有正确的 emit 定义', () => {
      const wrapper = mount(ModelForm)
      expect(typeof wrapper.vm.$emit).toBe('function')
    })
  })

  describe('Exposed 方法', () => {
    it('暴露 reset 方法', () => {
      const wrapper = mount(ModelForm)
      expect(typeof (wrapper.vm as any).reset).toBe('function')
    })

    it('暴露 setFormData 方法', () => {
      const wrapper = mount(ModelForm)
      expect(typeof (wrapper.vm as any).setFormData).toBe('function')
    })

    it('暴露 formData 属性', () => {
      const wrapper = mount(ModelForm)
      expect((wrapper.vm as any).formData).toBeDefined()
    })

    it('暴露 apiKeyChanged 属性', () => {
      const wrapper = mount(ModelForm)
      expect((wrapper.vm as any).apiKeyChanged).toBeDefined()
    })
  })
})
