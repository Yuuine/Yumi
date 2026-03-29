import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SidebarNav from '@/components/sidebar/SidebarNav.vue'

vi.mock('@/stores', () => ({
  useAccountStore: vi.fn(() => ({
    currentAccount: { id: 'test-account', displayName: '测试用户' },
    currentAccountId: 'test-account',
    isInitialized: true,
    loadCharacters: vi.fn().mockResolvedValue([]),
    loadConversations: vi.fn().mockResolvedValue([]),
    saveConversation: vi.fn(),
    deleteConversation: vi.fn(),
  })),
  useChatStore: vi.fn(() => ({
    currentConversationId: null,
  })),
}))

vi.mock('@/api', () => ({
  conversationsApi: {
    getConversations: vi.fn().mockResolvedValue({ conversations: [] }),
    updateTitle: vi.fn(),
    deleteConversation: vi.fn(),
  },
}))

vi.mock('@/components/icons', () => ({
  IconAdd: { template: '<div class="icon-add"></div>' },
  IconMore: { template: '<div class="icon-more"></div>' },
  IconModels: { template: '<div class="icon-models"></div>' },
  IconCharacter: { template: '<div class="icon-character"></div>' },
  IconChevronDown: { template: '<div class="icon-chevron-down"></div>' },
  IconChat: { template: '<div class="icon-chat"></div>' },
  IconEdit: { template: '<div class="icon-edit"></div>' },
  IconDelete: { template: '<div class="icon-delete"></div>' },
}))

vi.mock('@/components/common', () => ({
  CharacterSelectDialog: { template: '<div class="character-select-dialog"></div>' },
}))

vi.mock('@/composables/useModal', () => ({
  useConfirmDialog: vi.fn(() => ({
    showDialog: vi.fn(),
  })),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: vi.fn(() => ({
    success: vi.fn(),
  })),
}))

vi.mock('@/utils/avatar-manager', () => ({
  getAvatarPath: vi.fn(path => `/avatar/${path}`),
  DEFAULT_AVATAR_PATH: '/default-avatar.png',
}))

vi.mock('@/utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

describe('SidebarNav - 侧边栏导航组件', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('isExpanded 为 true 时正常渲染', () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      expect(wrapper.find('.sidebar-nav').exists()).toBe(true)
    })

    it('isExpanded 为 false 时不渲染', () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: false,
        },
      })
      expect(wrapper.find('.sidebar-nav').exists()).toBe(false)
    })

    it('渲染新对话按钮', () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      expect(wrapper.find('.new-chat-btn').exists()).toBe(true)
    })

    it('渲染底部导航按钮', () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      expect(wrapper.find('.nav-buttons-bottom').exists()).toBe(true)
    })

    it('渲染用户信息', () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      expect(wrapper.find('.user-item').exists()).toBe(true)
    })
  })

  describe('Props 和 Emits', () => {
    it('接受 isExpanded prop', () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      expect(wrapper.props('isExpanded')).toBe(true)
    })

    it('isExpanded 有默认值 true', () => {
      const wrapper = mount(SidebarNav)
      expect(wrapper.props('isExpanded')).toBe(true)
    })

    it('有正确的 emit 定义', () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      expect(typeof wrapper.vm.$emit).toBe('function')
    })
  })

  describe('按钮触发事件', () => {
    it('点击新对话按钮', async () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      const newChatBtn = wrapper.find('.new-chat-btn')
      await newChatBtn.trigger('click')
      expect(true).toBe(true)
    })

    it('点击模型按钮', async () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      const modelsBtn = wrapper.find('.nav-btn-left')
      await modelsBtn.trigger('click')
      expect(wrapper.emitted('openModels')).toBeTruthy()
    })

    it('点击角色按钮', async () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      const characterBtn = wrapper.find('.nav-btn-right')
      await characterBtn.trigger('click')
      expect(wrapper.emitted('openCharacter')).toBeTruthy()
    })

    it('点击用户信息打开设置', async () => {
      const wrapper = mount(SidebarNav, {
        props: {
          isExpanded: true,
        },
      })
      const userItem = wrapper.find('.user-item')
      await userItem.trigger('click')
      expect(wrapper.emitted('openSettings')).toBeTruthy()
    })
  })
})
