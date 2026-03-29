import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import AccountSettings from '@/components/settings/AccountSettings.vue'
import { useAccountStore, useAuthStore } from '@/stores'
import { useToast } from '@/composables/useToast'
import { useConfirmDialog } from '@/composables/useModal'

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

vi.mock('@/stores', () => ({
  useAccountStore: vi.fn(),
  useAuthStore: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: vi.fn(),
}))

vi.mock('@/composables/useModal', () => ({
  useConfirmDialog: vi.fn(),
}))

vi.mock('@/components/icons', () => ({
  IconCopy: { template: '<span class="icon-copy"></span>' },
  IconLogout: { template: '<span class="icon-logout"></span>' },
}))

const mockAccountStore = {
  currentAccount: null as any,
  accounts: [],
  currentConfig: null,
  isInitialized: false,
}

const mockAuthStore = {
  logout: vi.fn(),
}

const mockToast = {
  success: vi.fn(),
  warning: vi.fn(),
  error: vi.fn(),
}

const mockConfirmDialog = {
  showDialog: vi.fn(),
}

describe('AccountSettings', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    vi.mocked(useAccountStore).mockReturnValue(mockAccountStore as any)
    vi.mocked(useAuthStore).mockReturnValue(mockAuthStore as any)
    vi.mocked(useToast).mockReturnValue(mockToast as any)
    vi.mocked(useConfirmDialog).mockReturnValue(mockConfirmDialog as any)
  })

  it('renders correctly', () => {
    mockAccountStore.currentAccount = {
      id: 'test-account-id',
      displayName: '测试用户',
      createdAt: '2024-01-01T00:00:00.000Z',
    }

    const wrapper = mount(AccountSettings, {
      global: {
        stubs: {
          IconCopy: true,
          IconLogout: true,
        },
      },
    })

    expect(wrapper.find('.account-settings-content').exists()).toBe(true)
  })

  it('displays account information correctly', () => {
    mockAccountStore.currentAccount = {
      id: 'test-account-id',
      displayName: '测试用户',
      createdAt: '2024-01-01T00:00:00.000Z',
    }

    const wrapper = mount(AccountSettings, {
      global: {
        stubs: {
          IconCopy: true,
          IconLogout: true,
        },
      },
    })

    expect(wrapper.text()).toContain('测试用户')
    expect(wrapper.text()).toContain('test-account-id')
  })

  it('shows copy button when account ID exists', () => {
    mockAccountStore.currentAccount = {
      id: 'test-account-id',
      displayName: '测试用户',
      createdAt: '2024-01-01T00:00:00.000Z',
    }

    const wrapper = mount(AccountSettings, {
      global: {
        stubs: {
          IconCopy: true,
          IconLogout: true,
        },
      },
    })

    expect(wrapper.find('.copy-btn').exists()).toBe(true)
  })

  it('displays logout button', () => {
    mockAccountStore.currentAccount = {
      id: 'test-account-id',
      displayName: '测试用户',
      createdAt: '2024-01-01T00:00:00.000Z',
    }

    const wrapper = mount(AccountSettings, {
      global: {
        stubs: {
          IconCopy: true,
          IconLogout: true,
        },
      },
    })

    expect(wrapper.find('.logout-btn').exists()).toBe(true)
  })

  it('shows placeholder when no account data', () => {
    mockAccountStore.currentAccount = null

    const wrapper = mount(AccountSettings, {
      global: {
        stubs: {
          IconCopy: true,
          IconLogout: true,
        },
      },
    })

    const infoValues = wrapper.findAll('.info-value')
    expect(infoValues.length).toBeGreaterThan(0)
  })
})
