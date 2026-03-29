import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ModelCard from '@/components/Models/ModelCard.vue'
import type { ModelConfig } from '@/types'

vi.mock('@/components/icons', () => ({
  IconLink: { template: '<span data-test="icon-link"></span>' },
  IconEdit: { template: '<span data-test="icon-edit"></span>' },
  IconCopy: { template: '<span data-test="icon-copy"></span>' },
  IconDelete: { template: '<span data-test="icon-delete"></span>' },
  IconDisable: { template: '<span data-test="icon-disable"></span>' },
  IconSuccess: { template: '<span data-test="icon-success"></span>' },
}))

vi.mock('@/constants', () => ({
  PROVIDER_NAMES: {
    deepseek: 'DeepSeek',
    openai: 'OpenAI',
  },
  getModelCapabilities: vi.fn(() => ({
    toolCall: false,
    reasoning: false,
    webSearch: false,
    multimodal: false,
  })),
}))

const mockModel: ModelConfig = {
  id: 'model-1',
  providerId: 'deepseek',
  name: 'Test Model',
  baseUrl: 'https://api.example.com',
  apiKey: 'test-api-key',
  modelName: 'deepseek-chat',
  modelType: 'text',
  maxTokens: 4096,
  temperature: 0.7,
  isEnabled: true,
  isTested: true,
  testStatus: 'passed',
  editCount: 0,
}

describe('ModelCard - 模型卡片组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('可以正常渲染', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.find('.model-card').exists()).toBe(true)
    })

    it('显示模型名称', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.find('.model-name').text()).toBe(mockModel.name)
    })

    it('显示提供商标签', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.find('.tag-provider').exists()).toBe(true)
    })

    it('显示模型名称标签', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.find('.tag-model').text()).toBe(mockModel.modelName)
    })

    it('显示已启用标签当模型启用时', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: { ...mockModel, isEnabled: true },
        },
      })
      expect(wrapper.find('.tag-enabled').exists()).toBe(true)
    })

    it('显示已禁用标签当模型禁用时', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: { ...mockModel, isEnabled: false },
        },
      })
      expect(wrapper.find('.tag-disabled').exists()).toBe(true)
    })
  })

  describe('按钮渲染', () => {
    it('渲染所有操作按钮', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      const buttons = wrapper.findAll('.action-btn')
      expect(buttons.length).toBe(5)
    })

    it('测试按钮存在', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.text()).toContain('测试')
    })

    it('编辑按钮存在', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.text()).toContain('编辑')
    })

    it('克隆按钮存在', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.text()).toContain('克隆')
    })

    it('启用/禁用按钮存在', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.text()).toContain('禁用')
    })

    it('删除按钮存在', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.text()).toContain('删除')
    })

    it('测试时禁用所有按钮', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
          isTesting: true,
        },
      })
      const buttons = wrapper.findAll('button')
      buttons.forEach(button => {
        expect(button.attributes('disabled')).toBeDefined()
      })
    })
  })

  describe('Props', () => {
    it('接受 model prop', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      expect(wrapper.props('model')).toEqual(mockModel)
    })

    it('接受可选的 isTesting prop', () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
          isTesting: true,
        },
      })
      expect(wrapper.props('isTesting')).toBe(true)
    })
  })

  describe('Emits', () => {
    it('点击测试按钮时触发 test event', async () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      const testButton = wrapper.findAll('.action-btn')[0]
      await testButton.trigger('click')
      expect(wrapper.emitted('test')).toHaveLength(1)
    })

    it('点击编辑按钮时触发 edit event', async () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      const editButton = wrapper.findAll('.action-btn')[1]
      await editButton.trigger('click')
      expect(wrapper.emitted('edit')).toHaveLength(1)
    })

    it('点击克隆按钮时触发 clone event', async () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      const cloneButton = wrapper.findAll('.action-btn')[2]
      await cloneButton.trigger('click')
      expect(wrapper.emitted('clone')).toHaveLength(1)
    })

    it('点击切换按钮时触发 toggle event', async () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      const toggleButton = wrapper.findAll('.action-btn')[3]
      await toggleButton.trigger('click')
      expect(wrapper.emitted('toggle')).toHaveLength(1)
    })

    it('点击删除按钮时触发 delete event', async () => {
      const wrapper = mount(ModelCard, {
        props: {
          model: mockModel,
        },
      })
      const deleteButton = wrapper.findAll('.action-btn')[4]
      await deleteButton.trigger('click')
      expect(wrapper.emitted('delete')).toHaveLength(1)
    })
  })
})
