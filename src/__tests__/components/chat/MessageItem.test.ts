import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageItem from '@/components/chat/MessageItem.vue'

vi.mock('@/utils', () => ({
  copyToClipboard: vi.fn().mockResolvedValue(true),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: vi.fn(() => ({
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  })),
}))

vi.mock('@/components/common/MarkdownRenderer.vue', () => ({
  default: { template: '<div class="markdown-renderer"></div>' },
}))

vi.mock('@/components/chat/MessageActionsFooter.vue', () => ({
  default: { template: '<div class="message-actions-footer"></div>' },
}))

describe('MessageItem - 消息项组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('可以正常渲染用户消息', () => {
      const wrapper = mount(MessageItem, {
        props: {
          message: {
            id: '1',
            role: 'user',
            content: 'Hello',
            timestamp: Date.now(),
          },
        },
      })
      expect(wrapper.find('.message-item').exists()).toBe(true)
      expect(wrapper.find('.message-item').classes()).toContain('user')
    })

    it('可以正常渲染助手消息', () => {
      const wrapper = mount(MessageItem, {
        props: {
          message: {
            id: '2',
            role: 'assistant',
            content: 'Hi there',
            timestamp: Date.now(),
          },
        },
      })
      expect(wrapper.find('.message-item').exists()).toBe(true)
      expect(wrapper.find('.message-item').classes()).toContain('assistant')
    })

    it('显示消息内容', () => {
      const testContent = 'Test message content'
      const wrapper = mount(MessageItem, {
        props: {
          message: {
            id: '1',
            role: 'user',
            content: testContent,
            timestamp: Date.now(),
          },
        },
      })
      expect(wrapper.text()).toContain(testContent)
    })
  })

  describe('Props 和 Emits', () => {
    it('接受 message prop', () => {
      const testMessage = {
        id: '1',
        role: 'user',
        content: 'Test',
        timestamp: Date.now(),
      }
      const wrapper = mount(MessageItem, {
        props: {
          message: testMessage,
        },
      })
      expect(wrapper.props('message')).toEqual(testMessage)
    })

    it('有正确的 emit 定义', () => {
      const wrapper = mount(MessageItem, {
        props: {
          message: {
            id: '1',
            role: 'user',
            content: 'Test',
            timestamp: Date.now(),
          },
        },
      })
      expect(typeof wrapper.vm.$emit).toBe('function')
    })
  })
})
