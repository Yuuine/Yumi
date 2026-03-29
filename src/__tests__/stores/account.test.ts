import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAccountStore } from '@/stores/account'

vi.mock('@/utils/device-fingerprint', () => ({
  generateDeviceFingerprint: vi.fn().mockResolvedValue({
    fingerprint: 'test-fingerprint-123',
  }),
}))

vi.mock('@/utils/avatar-manager', () => ({
  getRandomAvatar: vi.fn().mockReturnValue('test-avatar'),
}))

vi.mock('@/utils/crypto-service', () => ({
  encrypt: vi.fn().mockResolvedValue({ ciphertext: 'encrypted-data', iv: 'iv', salt: 'salt' }),
  decrypt: vi.fn().mockResolvedValue('decrypted-data'),
}))

vi.mock('@/utils/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}))

vi.mock('@/api', () => ({
  userApi: {
    listUsers: vi.fn().mockResolvedValue({ users: [] }),
    getFullAccountData: vi.fn().mockResolvedValue({
      createdAt: '2024-01-01',
      updatedAt: '2024-01-02',
      roleName: '测试用户',
    }),
    getProfile: vi.fn().mockResolvedValue({ roleName: '测试用户' }),
    updateProfile: vi.fn().mockResolvedValue({}),
    purgeUserData: vi.fn().mockResolvedValue({}),
  },
  characterCardsApi: {
    list: vi.fn().mockResolvedValue([]),
    listCharacterCards: vi.fn().mockResolvedValue({ cards: [] }),
    upsert: vi.fn().mockResolvedValue({}),
    remove: vi.fn().mockResolvedValue({}),
  },
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    accessToken: null,
    userId: null,
    nickname: null,
    isAuthenticated: false,
    validateToken: vi.fn(),
  }),
}))

vi.mock('@/utils', () => ({
  generateAccountId: vi.fn().mockReturnValue('test-account-id'),
  generateCharacterId: vi.fn().mockReturnValue('test-character-id'),
  generateConversationId: vi.fn().mockReturnValue('test-conversation-id'),
  generateMessageId: vi.fn().mockReturnValue('test-message-id'),
  generateSecretId: vi.fn().mockReturnValue('test-secret-id'),
  buildChecksumSource: vi.fn().mockReturnValue('checksum-source'),
  sha256Hex: vi.fn().mockReturnValue('test-checksum'),
  isEncryptedData: vi.fn().mockReturnValue(false),
  isAccountExportData: vi.fn().mockReturnValue(true),
  countMessages: vi.fn().mockReturnValue(0),
  decryptModelSecrets: vi.fn().mockReturnValue([]),
  remapImportIds: vi
    .fn()
    .mockReturnValue({ mappedCharacters: {}, mappedConversations: {}, finalConfig: {} }),
}))

const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('useAccountStore - 基础状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  it('初始化状态正确', () => {
    const store = useAccountStore()

    expect(store.accounts).toEqual([])
    expect(store.currentAccount).toBeNull()
    expect(store.currentConfig).toBeNull()
    expect(store.isInitialized).toBe(false)
    expect(store.isLoading).toBe(false)
  })

  it('hasAccounts 计算正确', async () => {
    const store = useAccountStore()

    expect(store.hasAccounts).toBe(false)

    await store.createDefaultAccount()

    expect(store.hasAccounts).toBe(true)
  })
})

describe('useAccountStore - 账户管理功能', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  it('createDefaultAccount 创建默认账户成功', async () => {
    const store = useAccountStore()

    const account = await store.createDefaultAccount()

    expect(account).toBeTruthy()
    expect(account.id).toBe('test-account-id')
    expect(account.displayName).toBe('默认账号')
    expect(store.accounts.length).toBe(1)
    expect(store.currentAccount).toEqual(account)
  })

  it('createAccount 创建自定义账户成功', async () => {
    const store = useAccountStore()

    const account = await store.createAccount('测试账号')

    expect(account).toBeTruthy()
    expect(account.id).toBe('test-account-id')
    expect(account.displayName).toBe('测试账号')
    expect(store.accounts.length).toBe(1)
    expect(store.currentAccount).toEqual(account)
  })

  it('createAccount 支持自定义角色和对话', async () => {
    const store = useAccountStore()
    const customCharacter = {
      id: 'custom-char-id',
      name: '自定义角色',
      isActive: true,
      roleOverview: '测试角色',
      appearance: {
        race: '人类',
        gender: '女',
        visualAge: '20岁',
        actualAge: '20岁',
        location: '测试',
        description: '测试描述',
      },
      personality: {
        core: '测试',
        selfPerception: '测试',
        attitudeToUser: '测试',
        likes: '测试',
        dislikes: '测试',
      },
      communication: {
        toneBase: '测试',
        wordHabits: '测试',
        emotionRules: '测试',
        lengthPref: '测试',
      },
      specialLogic: '测试',
      fewShotExamples: '测试',
      avatar: 'test-avatar',
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    }
    const customConversation = {
      id: 'custom-conv-id',
      title: '自定义对话',
    }

    const account = await store.createAccount('带角色账号', customCharacter, customConversation)

    expect(account).toBeTruthy()
    expect(store.currentConfig?.activeCharacterId).toBe('custom-char-id')
  })

  it('updateAccountProfile 更新账户信息成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()

    await store.updateAccountProfile({ displayName: '更新后的账号' })

    expect(store.currentAccount?.displayName).toBe('更新后的账号')
  })

  it('switchAccount 切换账户成功', async () => {
    const store = useAccountStore()

    await store.createAccount('账号1')
    const account1Id = store.currentAccount!.id

    vi.mocked(await import('@/utils')).generateAccountId.mockReturnValue('test-account-id-2')
    await store.createAccount('账号2')
    const account2Id = store.currentAccount!.id

    expect(store.accounts.length).toBe(2)

    await store.switchAccount(account1Id)
    expect(store.currentAccount?.id).toBe(account1Id)
  })

  it('switchAccount 切换不存在的账户抛出错误', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()

    await expect(store.switchAccount('non-existent-id')).rejects.toThrow()
  })

  it('deleteAccount 删除账户成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()
    const accountId = store.currentAccount!.id

    expect(store.accounts.length).toBe(1)

    await store.deleteAccount(accountId)

    expect(store.accounts.length).toBe(0)
    expect(store.currentAccount).toBeNull()
  })
})

describe('useAccountStore - 角色管理功能', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  it('createNewCharacterTemplate 创建默认角色模板', async () => {
    const store = useAccountStore()

    const character = store.createNewCharacterTemplate()

    expect(character).toBeTruthy()
    expect(character.id).toBe('test-character-id')
    expect(character.name).toBe('艾拉')
    expect(character.avatar).toBe('test-avatar')
  })

  it('createBlankCharacter 创建空白角色', async () => {
    const store = useAccountStore()

    const character = store.createBlankCharacter()

    expect(character).toBeTruthy()
    expect(character.id).toBe('test-character-id')
    expect(character.name).toBe('艾拉')
  })

  it('saveCharacter 保存角色成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()
    const character = store.createBlankCharacter()

    const characterId = await store.saveCharacter(character)

    expect(characterId).toBe('test-character-id')

    const savedCharacters = await store.loadCharacters()
    expect(savedCharacters.length).toBeGreaterThan(0)
  })

  it('getCharacter 获取角色成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()
    const character = store.createBlankCharacter()
    const characterId = await store.saveCharacter(character)

    const retrievedCharacter = await store.getCharacter(characterId)

    expect(retrievedCharacter).toBeTruthy()
    expect(retrievedCharacter?.id).toBe(characterId)
  })

  it('getCharacter 获取不存在的角色返回null', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()

    const character = await store.getCharacter('non-existent-id')

    expect(character).toBeNull()
  })

  it('deleteCharacter 删除角色成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()
    const character = store.createBlankCharacter()
    const characterId = await store.saveCharacter(character)

    const charactersBefore = await store.loadCharacters()
    expect(charactersBefore.length).toBeGreaterThan(0)

    await store.deleteCharacter(characterId)

    const charactersAfter = await store.loadCharacters()
    expect(charactersAfter.length).toBe(0)
  })
})

describe('useAccountStore - 对话管理功能', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  it('saveConversation 保存对话成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()

    const conversationId = await store.saveConversation({
      title: '新对话',
    })

    expect(conversationId).toBe('test-conversation-id')
  })

  it('loadConversations 加载对话成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()

    await store.saveConversation({ title: '对话1' })
    vi.mocked(await import('@/utils')).generateConversationId.mockReturnValue(
      'test-conversation-id-2'
    )
    await store.saveConversation({ title: '对话2' })

    const conversations = await store.loadConversations()

    expect(Array.isArray(conversations)).toBe(true)
    expect(conversations.length).toBeGreaterThan(0)
  })

  it('getConversation 获取对话成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()
    const conversationId = await store.saveConversation({ title: '测试对话' })

    const conversation = await store.getConversation(conversationId)

    expect(conversation).toBeTruthy()
  })

  it('getConversation 获取不存在的对话返回null', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()

    const conversation = await store.getConversation('non-existent-id')

    expect(conversation).toBeNull()
  })

  it('deleteConversation 删除对话成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()
    const conversationId = await store.saveConversation({ title: '要删除的对话' })

    await store.deleteConversation(conversationId)

    const conversation = await store.getConversation(conversationId)
    expect(conversation).toBeNull()
  })

  it('saveMessage 保存消息成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()
    const conversationId = await store.saveConversation({ title: '对话' })

    const messageId = await store.saveMessage(conversationId, {
      role: 'user',
      content: '你好',
    })

    expect(messageId).toBe('test-message-id')

    const messages = await store.loadMessages(conversationId)
    expect(messages.length).toBe(1)
  })
})

describe('useAccountStore - 配置功能', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  it('updateAccountConfig 更新配置成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()

    expect(store.currentConfig?.preferences.theme).toBe('dark')

    await store.updateAccountConfig({
      preferences: {
        ...store.currentConfig!.preferences,
        theme: 'light',
      },
    })

    expect(store.currentConfig?.preferences.theme).toBe('light')
  })

  it('setActiveCharacterId 设置活跃角色成功', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()
    const character = store.createBlankCharacter()
    const characterId = await store.saveCharacter(character)

    await store.setActiveCharacterId(characterId)

    expect(store.currentConfig?.activeCharacterId).toBe(characterId)
  })
})

describe('useAccountStore - 统计功能', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  it('getAccountStats 返回正确的统计数据', async () => {
    const store = useAccountStore()
    await store.createDefaultAccount()

    const character = store.createBlankCharacter()
    await store.saveCharacter(character)

    await store.saveConversation({ title: '对话1' })

    const stats = await store.getAccountStats()

    expect(stats).toBeTruthy()
    expect(typeof stats.characterCount).toBe('number')
    expect(typeof stats.conversationCount).toBe('number')
    expect(typeof stats.dataSize).toBe('number')
  })

  it('getAccountStats 无账户时返回零值', async () => {
    const store = useAccountStore()

    const stats = await store.getAccountStats()

    expect(stats.characterCount).toBe(0)
    expect(stats.conversationCount).toBe(0)
    expect(stats.dataSize).toBe(0)
  })
})

describe('useAccountStore - 本地存储', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  it('数据正确保存到localStorage', async () => {
    const store = useAccountStore()
    await store.createAccount('测试存储账号')

    expect(localStorageMock.setItem).toHaveBeenCalled()
    expect(localStorageMock.getItem('yumi_accounts')).not.toBeNull()
  })

  it('数据正确从localStorage加载', async () => {
    const store = useAccountStore()
    await store.createAccount('测试存储账号')

    const accountId = store.currentAccount!.id
    const storedData = localStorageMock.getItem(`yumi_account_${accountId}`)

    expect(storedData).not.toBeNull()

    const parsedData = JSON.parse(storedData!)
    expect(parsedData.profile.displayName).toBe('测试存储账号')
  })
})
