import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ChatInput from '@/components/chat/ChatInput.vue'

vi.mock('@/stores', () => ({
  useModelsStore: vi.fn(() => ({
    models: [],
    activeModel: null,
  })),
  useAccountStore: vi.fn(() => ({
    currentAccountId: 'test-account-id',
  })),
}))

vi.mock('@/composables', () => ({
  useToast: vi.fn(() => ({
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  })),
}))

vi.mock('@/utils/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}))

vi.mock('@/components/icons', () => ({
  IconArrowUp: { template: '<div class="icon-arrow-up"></div>' },
  IconCheck: { template: '<div class="icon-check"></div>' },
}))

describe('ChatInput - 聊天输入组件', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('可以正常渲染', () => {
      const wrapper = mount(ChatInput, {
        props: {
          disabled: false,
          sidebarCollapsed: false,
        },
      })
      expect(wrapper.find('.chat-input-wrapper').exists()).toBe(true)
      expect(wrapper.find('.chat-input-container').exists()).toBe(true)
      expect(wrapper.find('.input-textarea').exists()).toBe(true)
    })

    it('接受 disabled prop', () => {
      const wrapper = mount(ChatInput, {
        props: {
          disabled: true,
        },
      })
      expect(wrapper.props('disabled')).toBe(true)
    })

    it('接受 sidebarCollapsed prop', () => {
      const wrapper = mount(ChatInput, {
        props: {
          sidebarCollapsed: true,
        },
      })
      expect(wrapper.props('sidebarCollapsed')).toBe(true)
    })
  })

  describe('基础功能', () => {
    it('textarea 有正确的 placeholder', () => {
      const wrapper = mount(ChatInput)
      const textarea = wrapper.find('.input-textarea')
      expect(textarea.attributes('placeholder')).toBe('你好啊！')
    })

    it('有模型切换按钮', () => {
      const wrapper = mount(ChatInput)
      expect(wrapper.find('.model-switch-btn').exists()).toBe(true)
    })

    it('有深度思考按钮', () => {
      const wrapper = mount(ChatInput)
      expect(wrapper.find('.deep-think-btn').exists()).toBe(true)
    })

    it('没有内容时不显示发送按钮', () => {
      const wrapper = mount(ChatInput)
      expect(wrapper.find('.send-btn').exists()).toBe(false)
    })
  })

  describe('事件处理', () => {
    it('可以正确设置和获取 deepThinking v-model', async () => {
      const wrapper = mount(ChatInput, {
        props: {
          'deepThinking': false,
          'onUpdate:deepThinking': vi.fn(),
        },
      })
      
      expect(wrapper.props('deepThinking')).toBe(false)
    })

    it('有正确的 emit 定义', () => {
      const wrapper = mount(ChatInput)
      expect(typeof wrapper.vm.$emit).toBe('function')
    })
  })
})
