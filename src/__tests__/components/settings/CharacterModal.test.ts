import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import CharacterModal from '@/components/settings/CharacterModal.vue'
import { useAccountStore } from '@/stores'
import { useToast } from '@/composables/useToast'

vi.mock('@/stores', () => ({
  useAccountStore: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: vi.fn(),
}))

vi.mock('@/api', () => ({
  conversationsApi: {
    getConversations: vi.fn(),
    deleteConversation: vi.fn(),
  },
}))

vi.mock('@/components/icons', () => ({
  IconClose: { template: '<span class="icon-close"></span>' },
}))

const mockAccountStore = {
  currentAccount: null,
  currentConfig: { activeCharacterId: 'char-1' },
  loadCharacters: vi.fn(),
  createBlankCharacter: vi.fn(),
  saveCharacter: vi.fn(),
  setActiveCharacterId: vi.fn(),
  getCharacter: vi.fn(),
  deleteCharacter: vi.fn(),
  deleteConversation: vi.fn(),
  loadConversations: vi.fn(),
}

const mockToast = {
  success: vi.fn(),
  warning: vi.fn(),
  error: vi.fn(),
}

const defaultStubs = {
  Teleport: { template: '<div><slot /></div>' },
  Transition: { template: '<div><slot /></div>' },
  IconClose: true,
  CharacterSettings: true,
}

describe('CharacterModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    
    vi.mocked(useAccountStore).mockReturnValue(mockAccountStore as any)
    vi.mocked(useToast).mockReturnValue(mockToast as any)
  })

  it('renders when visible is true', () => {
    const wrapper = mount(CharacterModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs
      }
    })
    
    expect(wrapper.find('.character-modal-overlay').exists()).toBe(true)
    expect(wrapper.find('.character-modal').exists()).toBe(true)
  })

  it('does not render when visible is false', () => {
    const wrapper = mount(CharacterModal, {
      props: { visible: false },
      global: {
        stubs: defaultStubs
      }
    })
    
    expect(wrapper.find('.character-modal-overlay').exists()).toBe(false)
  })

  it('renders modal title', () => {
    const wrapper = mount(CharacterModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs
      }
    })
    
    expect(wrapper.find('.modal-title').text()).toBe('角色配置')
  })

  it('renders toolbar buttons', () => {
    const wrapper = mount(CharacterModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs
      }
    })
    
    const toolbarButtons = wrapper.findAll('.toolbar-btn')
    expect(toolbarButtons.length).toBeGreaterThan(0)
  })

  it('renders close button', () => {
    const wrapper = mount(CharacterModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs
      }
    })
    
    expect(wrapper.find('.close-btn').exists()).toBe(true)
  })

  it('emits close event when close button is clicked', async () => {
    const wrapper = mount(CharacterModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs
      }
    })
    
    await wrapper.find('.close-btn').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('renders modal body with CharacterSettings component', () => {
    const wrapper = mount(CharacterModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs
      }
    })
    
    expect(wrapper.find('.modal-body').exists()).toBe(true)
  })
})
