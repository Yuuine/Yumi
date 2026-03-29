import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ChatView from '@/views/ChatView.vue'

vi.mock('@/stores', () => ({
  useChatStore: vi.fn(() => ({
    messages: [],
    isLoading: false,
    isStreaming: false,
    currentConversationId: null,
    sendMessage: vi.fn(),
    sendMessageStream: vi.fn(),
    startNewConversation: vi.fn(),
    switchConversation: vi.fn(),
    loadMoreMessages: vi.fn(),
  })),
  useAccountStore: vi.fn(() => ({
    initialize: vi.fn(),
    loadConversations: vi.fn(),
    currentAccountId: 'test-account-id',
  })),
  useModelsStore: vi.fn(() => ({
    models: [],
  })),
}))

vi.mock('@/composables', () => ({
  useToast: vi.fn(() => ({
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  })),
  useModalState: vi.fn(() => ({
    visible: false,
    open: vi.fn(),
    close: vi.fn(),
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

vi.mock('@/components/sidebar', () => ({
  SidebarNav: { template: '<div class="sidebar-nav"></div>' },
}))

vi.mock('@/components/chat', () => ({
  MessageList: {
    template: '<div class="message-list"></div>',
    methods: { scrollToBottom: vi.fn() },
  },
  ChatInput: { template: '<div class="chat-input"></div>' },
}))

vi.mock('@/components/icons', () => ({
  IconSidebarCollapse: { template: '<div class="icon-sidebar-collapse"></div>' },
  IconSidebarExpand: { template: '<div class="icon-sidebar-expand"></div>' },
}))

vi.mock('@/components/models/ModelsModal.vue', () => ({
  default: { template: '<div class="models-modal"></div>' },
}))

vi.mock('@/components/settings/CharacterModal.vue', () => ({
  default: { template: '<div class="character-modal"></div>' },
}))

vi.mock('@/components/settings/SettingsModal.vue', () => ({
  default: { template: '<div class="settings-modal"></div>' },
}))

describe('ChatView - 聊天页面', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('可以正常渲染聊天页面', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.chat-view').exists()).toBe(true)
    })

    it('显示侧边栏导航组件', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.sidebar-nav').exists()).toBe(true)
    })

    it('显示侧边栏切换按钮', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.toggle-button').exists()).toBe(true)
    })

    it('显示聊天主区域', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.chat-main').exists()).toBe(true)
    })

    it('显示消息列表组件', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.message-list').exists()).toBe(true)
    })

    it('显示聊天输入组件', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.chat-input').exists()).toBe(true)
    })

    it('显示模型模态框', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.models-modal').exists()).toBe(true)
    })

    it('显示角色模态框', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.character-modal').exists()).toBe(true)
    })

    it('显示设置模态框', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.settings-modal').exists()).toBe(true)
    })
  })

  describe('侧边栏默认状态', () => {
    it('默认侧边栏是展开的', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.toggle-button').classes()).toContain('sidebar-open')
    })

    it('侧边栏展开时 chat-main 有正确的类', () => {
      const wrapper = mount(ChatView)
      expect(wrapper.find('.chat-main').classes()).not.toContain('sidebar-collapsed')
    })
  })
})
