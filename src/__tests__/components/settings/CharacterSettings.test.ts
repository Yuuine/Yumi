import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import CharacterSettings from '@/components/settings/CharacterSettings.vue'
import { useAccountStore } from '@/stores'
import { useToast } from '@/composables/useToast'

vi.mock('@/stores', () => ({
  useAccountStore: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: vi.fn(),
}))

vi.mock('@/api/character-cards', () => ({
  characterCardsApi: {
    upsert: vi.fn(),
  },
}))

vi.mock('@/utils/character-card-mapper', () => ({
  nestedCharacterToFlat: vi.fn(),
}))

vi.mock('@/components/common/AutoResizeTextarea', () => ({
  default: { template: '<div class="auto-resize-textarea"></div>' },
}))

vi.mock('@/components/common/TagsInput', () => ({
  default: { template: '<div class="tags-input"></div>' },
}))

vi.mock('@/components/common/ConversationPairInput', () => ({
  default: { template: '<div class="conversation-pair-input"></div>' },
}))

const mockAccountStore = {
  currentAccount: null as any,
  currentAccountId: null,
  currentConfig: { activeCharacterId: 'char-1' },
  loadCharacters: vi.fn(),
  getCharacter: vi.fn(),
  setActiveCharacterId: vi.fn(),
  saveCharacter: vi.fn(),
  createBlankCharacter: vi.fn(),
  loadCurrentAccountData: vi.fn(),
}

const mockToast = {
  success: vi.fn(),
  warning: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
}

describe('CharacterSettings', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    vi.mocked(useAccountStore).mockReturnValue(mockAccountStore as any)
    vi.mocked(useToast).mockReturnValue(mockToast as any)
  })

  it('renders correctly', () => {
    const wrapper = mount(CharacterSettings, {
      global: {
        stubs: {
          AutoResizeTextarea: true,
          TagsInput: true,
          ConversationPairInput: true,
        },
      },
    })

    expect(wrapper.find('.character-settings').exists()).toBe(true)
  })

  it('shows loading state when no draft data', () => {
    mockAccountStore.currentAccount = null

    const wrapper = mount(CharacterSettings, {
      global: {
        stubs: {
          AutoResizeTextarea: true,
          TagsInput: true,
          ConversationPairInput: true,
        },
      },
    })

    expect(wrapper.find('.character-empty').exists()).toBe(true)
  })

  it('renders section navigation', async () => {
    mockAccountStore.currentAccount = { id: 'test-account' }
    mockAccountStore.loadCharacters.mockResolvedValue([
      {
        id: 'char-1',
        name: '测试角色',
      },
    ])
    mockAccountStore.getCharacter.mockResolvedValue({
      id: 'char-1',
      name: '测试角色',
      roleOverview: '这是一个测试角色的描述',
      personality: { core: [], selfPerception: [], attitudeToUser: [], likes: [], dislikes: [] },
      communication: { toneBase: [], wordHabits: '', emotionRules: '', lengthPref: '' },
      appearance: {
        race: '',
        gender: '男',
        visualAge: '',
        actualAge: '',
        location: '',
        description: '',
      },
      nickname: [],
      specialLogic: [],
      fewShotExamples: [],
    })

    const wrapper = mount(CharacterSettings, {
      global: {
        stubs: {
          AutoResizeTextarea: true,
          TagsInput: true,
          ConversationPairInput: true,
        },
      },
    })

    await new Promise(resolve => setTimeout(resolve, 0))

    expect(wrapper.find('.section-nav').exists()).toBe(true)
  })

  it('has correct section navigation items', async () => {
    mockAccountStore.currentAccount = { id: 'test-account' }
    mockAccountStore.loadCharacters.mockResolvedValue([
      {
        id: 'char-1',
        name: '测试角色',
      },
    ])
    mockAccountStore.getCharacter.mockResolvedValue({
      id: 'char-1',
      name: '测试角色',
      roleOverview: '这是一个测试角色的描述',
      personality: { core: [], selfPerception: [], attitudeToUser: [], likes: [], dislikes: [] },
      communication: { toneBase: [], wordHabits: '', emotionRules: '', lengthPref: '' },
      appearance: {
        race: '',
        gender: '男',
        visualAge: '',
        actualAge: '',
        location: '',
        description: '',
      },
      nickname: [],
      specialLogic: [],
      fewShotExamples: [],
    })

    const wrapper = mount(CharacterSettings, {
      global: {
        stubs: {
          AutoResizeTextarea: true,
          TagsInput: true,
          ConversationPairInput: true,
        },
      },
    })

    await new Promise(resolve => setTimeout(resolve, 0))

    const navItems = wrapper.findAll('.section-nav-item')
    expect(navItems.length).toBeGreaterThan(0)
  })

  it('renders config scroll container', async () => {
    mockAccountStore.currentAccount = { id: 'test-account' }
    mockAccountStore.loadCharacters.mockResolvedValue([
      {
        id: 'char-1',
        name: '测试角色',
      },
    ])
    mockAccountStore.getCharacter.mockResolvedValue({
      id: 'char-1',
      name: '测试角色',
      roleOverview: '这是一个测试角色的描述',
      personality: { core: [], selfPerception: [], attitudeToUser: [], likes: [], dislikes: [] },
      communication: { toneBase: [], wordHabits: '', emotionRules: '', lengthPref: '' },
      appearance: {
        race: '',
        gender: '男',
        visualAge: '',
        actualAge: '',
        location: '',
        description: '',
      },
      nickname: [],
      specialLogic: [],
      fewShotExamples: [],
    })

    const wrapper = mount(CharacterSettings, {
      global: {
        stubs: {
          AutoResizeTextarea: true,
          TagsInput: true,
          ConversationPairInput: true,
        },
      },
    })

    await new Promise(resolve => setTimeout(resolve, 0))

    expect(wrapper.find('.config-scroll').exists()).toBe(true)
  })
})
