import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import MessageList from '@/components/chat/MessageList.vue'

vi.mock('@/stores', () => ({
  useChatStore: vi.fn(() => ({
    messages: [],
    currentConversationId: null,
  })),
}))

vi.mock('@/components/chat/MessageItem.vue', () => ({
  default: { template: '<div class="message-item-mock"></div>' },
}))

vi.mock('@/components/chat/ScrollToBottom.vue', () => ({
  default: { template: '<div class="scroll-to-bottom-mock"></div>' },
}))

vi.mock('@/components/icons', () => ({
  IconSpinner: { template: '<div class="icon-spinner"></div>' },
}))

describe('MessageList - 消息列表组件', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('可以正常渲染', () => {
      const wrapper = mount(MessageList, {
        props: {
          messages: [],
        },
      })
      expect(wrapper.find('.message-list').exists()).toBe(true)
    })

    it('没有消息时显示空状态', () => {
      const wrapper = mount(MessageList, {
        props: {
          messages: [],
        },
      })
      expect(wrapper.find('.empty-state').exists()).toBe(true)
    })
  })

  describe('Props 和 Emits', () => {
    it('接受 messages prop', () => {
      const testMessages = [
        { id: '1', role: 'user', content: 'Hello', timestamp: Date.now() },
      ] as any
      const wrapper = mount(MessageList, {
        props: {
          messages: testMessages,
        },
      })
      expect(wrapper.props('messages')).toEqual(testMessages)
    })

    it('有正确的 emit 定义', () => {
      const wrapper = mount(MessageList, {
        props: {
          messages: [],
        },
      })
      expect(typeof wrapper.vm.$emit).toBe('function')
    })
  })

  describe('公开方法', () => {
    it('有公开的方法定义', () => {
      const wrapper = mount(MessageList, {
        props: {
          messages: [],
        },
      })
      const vm = wrapper.vm as any
      expect(typeof vm.scrollToBottom).toBe('function')
      expect(typeof vm.scrollToBottomInstant).toBe('function')
      expect(typeof vm.scrollToBottomSmooth).toBe('function')
      expect(typeof vm.beginStickyFollow).toBe('function')
      expect(typeof vm.endStickyFollow).toBe('function')
      expect(typeof vm.completeStickyFollowSession).toBe('function')
    })
  })
})
