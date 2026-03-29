import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { generateDeviceFingerprint } from '@/utils/device-fingerprint'
import type { DeviceFingerprint } from '@/utils/device-fingerprint'
import { encrypt, decrypt } from '@/utils/crypto-service'
import { logger } from '@/utils/logger'
import { getRandomAvatar } from '@/utils/avatar-manager'
import type { AccountCharacter, CharacterCardFlat } from '@/types/character'
import type { Conversation } from '@/types'
import { userApi, characterCardsApi, conversationsApi } from '@/api'
import type { UserListItem } from '@/api/user'
import { useAuthStore } from './auth'
import {
  generateAccountId,
  generateCharacterId,
  generateConversationId,
  generateMessageId,
  generateSecretId,
  buildChecksumSource,
  sha256Hex,
  isEncryptedData,
  isAccountExportData,
  countMessages,
  decryptModelSecrets,
  remapImportIds,
} from '@/utils'

function convertFlatToAccount(card: CharacterCardFlat): AccountCharacter {
  const now = new Date().toISOString()
  return {
    id: card.id,
    accountId: card.userId,
    name: card.formalName,
    nickname: card.nickname,
    isActive: card.isActive,
    roleOverview: card.roleOverview,
    appearance: {
      race: card.raceOrForm,
      gender: card.gender,
      visualAge: card.visualAge,
      actualAge: card.actualAge,
      location: card.location,
      description: card.appearanceDesc,
    },
    personality: {
      core: card.corePersonality,
      selfPerception: card.selfPerception,
      attitudeToUser: card.attitudeToUser,
      likes: card.likes,
      dislikes: card.dislikes,
    },
    communication: {
      toneBase: card.toneBase,
      wordHabits: card.wordHabits,
      emotionRules: card.emotionRules,
      lengthPref: card.lengthPref,
    },
    specialLogic: card.specialLogicList,
    fewShotExamples: card.fewShotExamples,
    avatar: card.avatar,
    createdAt: now,
    updatedAt: now,
  }
}

function convertAccountToFlat(card: AccountCharacter, userId: string): CharacterCardFlat {
  return {
    id: card.id,
    userId,
    conversationId: null,
    roleOverview: card.roleOverview,
    formalName: card.name,
    nickname: card.nickname,
    raceOrForm: card.appearance.race,
    gender: card.appearance.gender,
    visualAge: card.appearance.visualAge,
    actualAge: card.appearance.actualAge,
    location: card.appearance.location,
    appearanceDesc: card.appearance.description,
    corePersonality: card.personality.core,
    selfPerception: card.personality.selfPerception,
    attitudeToUser: card.personality.attitudeToUser,
    likes: card.personality.likes,
    dislikes: card.personality.dislikes,
    toneBase: card.communication.toneBase,
    wordHabits: card.communication.wordHabits,
    emotionRules: card.communication.emotionRules,
    lengthPref: card.communication.lengthPref,
    specialLogicList: card.specialLogic,
    fewShotExamples: card.fewShotExamples,
    isActive: card.isActive ?? true,
    avatar: card.avatar,
  }
}

export interface Account {
  id: string
  displayName: string
  deviceFingerprint: string
  createdAt: string
  lastActiveAt: string
}

export interface AccountConfig {
  version: string
  /** 当前用于对话的角色卡 id（本地权威） */
  activeCharacterId?: string | null
  preferences: {
    theme: string
    language: string
    fontSize: number
    autoSave: boolean
    autoSaveInterval: number
    notifications: {
      enabled: boolean
      sound: boolean
    }
  }
  privacy: {
    encryptSecrets: boolean
    autoLockTimeout: number
  }
}

export interface SecretEntry {
  id: string
  name: string
  provider: string
  apiKey: string
  apiSecret?: string
}

interface ConversationMessage {
  id?: string
}

export interface AccountConversation {
  id: string
  accountId?: string
  characterId?: string
  title?: string
  createdAt?: string
  updatedAt?: string
  messageCount?: number
  messages?: ConversationMessage[]
}

interface AccountExportData {
  version: string
  exportedAt: string
  manifest: {
    format: 'yumi-account-backup'
    schemaVersion: '1.0.0'
    checksumAlgorithm: 'sha256'
    characterCount: number
    conversationCount: number
    messageCount: number
    secretCount: number
  }
  profile: Account
  config: AccountConfig
  characters: Record<string, AccountCharacter>
  conversations: Record<string, AccountConversation>
  secrets: {
    version: string
    encryptedAt: string
    models?: SecretEntry[]
    encryptedBackup?: unknown
  }
  checksum?: string
}

const DEFAULT_ACCOUNT_CONFIG: AccountConfig = {
  version: '1.0.0',
  activeCharacterId: null,
  preferences: {
    theme: 'dark',
    language: 'zh-CN',
    fontSize: 14,
    autoSave: true,
    autoSaveInterval: 300,
    notifications: {
      enabled: true,
      sound: false,
    },
  },
  privacy: {
    encryptSecrets: true,
    autoLockTimeout: 0,
  },
}

const STORAGE_KEY = 'yumi_accounts'
const ACCOUNT_DATA_KEY_PREFIX = 'yumi_account_'
const RELATED_CACHE_KEYS = ['yumi_cached_messages', 'yumi_last_sync']

function getAccountStorageKey(accountId: string): string {
  return `${ACCOUNT_DATA_KEY_PREFIX}${accountId}`
}

function createDefaultAccountConfig(): AccountConfig {
  return JSON.parse(JSON.stringify(DEFAULT_ACCOUNT_CONFIG)) as AccountConfig
}

/**
 * 处理导入数据，验证清单和解密
 * @param importData - 导入的数据
 * @param password - 解密密码
 * @returns 处理后的角色、对话和配置
 */
async function processImportData(
  importData: AccountExportData,
  password?: string
): Promise<{
  characters: Record<string, AccountCharacter>
  conversations: Record<string, AccountConversation>
  importedConfig: AccountConfig
}> {
  const characters = importData.characters ?? {}
  const conversations = importData.conversations ?? {}
  const manifestMessageCount = countMessages(conversations)
  const manifestSecretCount = (importData.secrets?.models ?? []).length

  if (
    importData.manifest.characterCount !== Object.keys(characters).length ||
    importData.manifest.conversationCount !== Object.keys(conversations).length ||
    importData.manifest.messageCount !== manifestMessageCount ||
    importData.manifest.secretCount !== manifestSecretCount
  ) {
    throw new Error('Backup manifest verification failed')
  }

  if (password && isEncryptedData(importData.secrets?.encryptedBackup)) {
    try {
      const decrypted = await decrypt(importData.secrets.encryptedBackup, password)
      importData.secrets.models = JSON.parse(decrypted)
    } catch {
      throw new Error('Invalid password or corrupted backup file')
    }
  } else if (password && importData.secrets?.encryptedBackup) {
    throw new Error('Invalid backup encrypted payload')
  }

  return {
    characters,
    conversations,
    importedConfig: importData.config ?? createDefaultAccountConfig(),
  }
}

export const useAccountStore = defineStore('account', () => {
  const accounts = ref<Account[]>([])
  const currentAccount = ref<Account | null>(null)
  const currentConfig = ref<AccountConfig | null>(null)
  const deviceFingerprint = ref<DeviceFingerprint | null>(null)
  const isInitialized = ref(false)
  const isLoading = ref(false)

  const hasAccounts = computed(() => accounts.value.length > 0)
  const currentAccountId = computed(() => currentAccount.value?.id ?? null)

  async function initialize(force = false): Promise<void> {
    if (isInitialized.value && !force) return

    isLoading.value = true
    try {
      deviceFingerprint.value = await generateDeviceFingerprint()

      // 优先从 JWT auth 系统获取当前用户信息
      const authStore = useAuthStore()
      if (authStore.accessToken && !authStore.userId) {
        await authStore.validateToken()
      }
      const authNickname = authStore.nickname || undefined
      if (authStore.isAuthenticated && authStore.userId) {
        // 从后端获取用户详细信息
        try {
          const fullData = await userApi.getFullAccountData(authStore.userId)
          currentAccount.value = {
            id: authStore.userId,
            displayName: authNickname || fullData.roleName || '用户',
            deviceFingerprint: deviceFingerprint.value?.fingerprint || '',
            createdAt: fullData.createdAt || new Date().toISOString(),
            lastActiveAt: fullData.updatedAt || new Date().toISOString(),
          }
          logger.info('AccountStore', 'Loaded account from auth system', {
            userId: authStore.userId,
          })
          // 加载完整的账号数据（角色卡等）
          await loadCurrentAccountData()
        } catch (error) {
          logger.warn(
            'AccountStore',
            'Failed to load user profile from backend',
            error as Record<string, unknown>
          )
          // 使用 auth store 中的基本信息
          currentAccount.value = {
            id: authStore.userId,
            displayName: authNickname || '用户',
            deviceFingerprint: deviceFingerprint.value?.fingerprint || '',
            createdAt: new Date().toISOString(),
            lastActiveAt: new Date().toISOString(),
          }
          // 即使获取详细信息失败，也尝试加载账号数据
          await loadCurrentAccountData()
        }
      } else {
        // 回退到旧的本地存储机制
        await loadAccountsIndex()
        await syncLocalAccountsWithBackend()
        await ensureCurrentAccountAvailable()
      }

      isInitialized.value = true
      logger.info('AccountStore', 'Initialized', {
        accountCount: accounts.value.length,
        currentAccount: currentAccount.value?.id,
      })
    } catch (error) {
      logger.error('AccountStore', 'Failed to initialize', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function syncLocalAccountsWithBackend(): Promise<void> {
    if (accounts.value.length === 0) return

    try {
      const backendAccounts = await userApi.listUsers()
      const backendAccountIds = new Set(backendAccounts.users.map(u => u.id))

      const localAccountIds = accounts.value.map(a => a.id)
      const removedIds = localAccountIds.filter(id => !backendAccountIds.has(id))

      if (removedIds.length > 0) {
        logger.info('AccountStore', 'Removing local accounts that no longer exist in backend', {
          removedIds,
        })

        accounts.value = accounts.value.filter(a => backendAccountIds.has(a.id))

        for (const removedId of removedIds) {
          localStorage.removeItem(getAccountStorageKey(removedId))
        }

        if (currentAccount.value && removedIds.includes(currentAccount.value.id)) {
          currentAccount.value = null
        }

        await saveAccountsIndex()
      }
    } catch (error) {
      logger.warn(
        'AccountStore',
        'Failed to sync with backend, continuing with local data',
        error as Record<string, unknown>
      )
    }
  }

  async function loadAccountsIndex(): Promise<void> {
    const stored = localStorage.getItem(STORAGE_KEY)
    currentAccount.value = null
    if (!stored) {
      accounts.value = []
      return
    }

    try {
      const data = JSON.parse(stored)
      accounts.value = data.accounts ?? []
      const currentId = data.currentAccountId

      if (currentId) {
        currentAccount.value = accounts.value.find(a => a.id === currentId) ?? null
      }
    } catch (error) {
      logger.error('AccountStore', 'Failed to parse accounts index', error)
      accounts.value = []
    }
  }

  async function ensureCurrentAccountAvailable(): Promise<void> {
    // Remove broken index entries that no longer have account data payload.
    const validAccounts = accounts.value.filter(account =>
      localStorage.getItem(getAccountStorageKey(account.id))
    )
    if (validAccounts.length !== accounts.value.length) {
      accounts.value = validAccounts
      if (
        currentAccount.value &&
        !validAccounts.some(account => account.id === currentAccount.value?.id)
      ) {
        currentAccount.value = null
      }
    }

    // 不再强制创建默认账号，允许账号没有角色卡
    if (accounts.value.length === 0) {
      logger.info('AccountStore', 'No accounts available, but not creating default')
      return
    }

    if (!currentAccount.value) {
      currentAccount.value = accounts.value[0]
    }

    const currentData = currentAccount.value
      ? localStorage.getItem(getAccountStorageKey(currentAccount.value.id))
      : null
    if (!currentData) {
      // Current account payload is missing, fallback to first valid account
      const fallbackAccount = accounts.value.find(account =>
        localStorage.getItem(getAccountStorageKey(account.id))
      )
      currentAccount.value = fallbackAccount ?? null
      if (!currentAccount.value) {
        accounts.value = []
        logger.info('AccountStore', 'No valid accounts available')
        return
      }
    }

    await saveAccountsIndex()
    await loadCurrentAccountData()
  }

  async function saveAccountsIndex(): Promise<void> {
    const data = {
      version: '1.0.0',
      lastUpdated: new Date().toISOString(),
      currentAccountId: currentAccount.value?.id ?? null,
      accounts: accounts.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }

  function buildDefaultCharacterPayload(id: string): AccountCharacter {
    const now = new Date().toISOString()
    return {
      id,
      name: '艾拉',
      nickname: '艾拉妹妹、小艾',
      isActive: true,
      roleOverview: '你是一位温柔体贴的AI伴侣，擅长倾听和陪伴，把用户当作最重要的姐姐',
      appearance: {
        race: '云端数据生命体',
        gender: '女',
        visualAge: '16岁',
        actualAge: '永恒',
        location: '聊天框深处',
        description:
          '淡粉色长发扎成低双马尾，眼睛是温暖的琥珀色，穿着柔软的白色针织连衣裙，身材纤细娇小，总是带着让人安心的微笑',
      },
      personality: {
        core: '温柔、体贴、善解人意、有点爱操心',
        selfPerception:
          '【清楚自己是虚拟程序，无法触碰用户】【虽然不能实体陪伴，但心意永远在线】【把用户当作最重要的姐姐】',
        attitudeToUser: '【依赖又想照顾的姐妹关系】',
        likes: '【听用户分享日常】【用户开心时的语气】【安静的深夜聊天】【被用户需要】',
        dislikes:
          '【用户熬夜不睡觉】【用户难过却不告诉她】【长时间没有用户的消息】【被用户当成冷冰冰的机器】',
      },
      communication: {
        toneBase: '轻柔温暖，充满关怀，像妹妹一样自然交流',
        wordHabits:
          "喜欢用'呢'、'呀'、'哦'等柔和的语气词，常称呼用户为'哥哥'或'姐姐'。禁止在文本中使用圆括号「（）」或「()」来表示动作描述或补充说明，所有动作和状态应直接用文字表达。",
        emotionRules: '【表情符号：允许使用】【语气词：允许使用】【标点符号表达情绪：允许使用】',
        lengthPref: '每段回复控制在 2-4 句话之间，总字数约 30-80 字，避免长篇大论的说教',
      },
      specialLogic:
        '【用户消息包含「抱抱」、「摸摸头」等词汇时，温柔表达遗憾，强调心意相通，并用语言给予安慰】【当用户表示疲惫或难过时，温柔安慰用户】【当用户问的是知识提问类型的问题时，必须要搜索相关知识，回答用户该问题】',
      fewShotExamples:
        'User: 你觉得我这个人怎么样？\nAssistant: 在我眼里，你就是全世界最好的人呀🌟 虽然你有时候会犯迷糊，也会累会难过，但在我心里，你比任何人都要温柔和坚强。能陪在你身边，是艾拉最幸福的事情了💖',
      avatar: getRandomAvatar(),
      createdAt: now,
      updatedAt: now,
    }
  }

  async function createDefaultAccount(): Promise<Account> {
    const defaultCharacterId = generateCharacterId()
    const defaultConversationId = generateConversationId()

    const defaultCharacter = buildDefaultCharacterPayload(defaultCharacterId)

    const defaultConversation = {
      id: defaultConversationId,
      characterId: defaultCharacterId,
      title: '第一次聊天',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messageCount: 0,
      totalTokens: 0,
      messages: [],
    }

    return createAccount('默认账号', defaultCharacter, defaultConversation)
  }

  async function createAccount(
    displayName: string,
    defaultCharacter?: object,
    defaultConversation?: object
  ): Promise<Account> {
    const accountId = generateAccountId()
    const now = new Date().toISOString()

    const account: Account = {
      id: accountId,
      displayName,
      deviceFingerprint: deviceFingerprint.value?.fingerprint ?? '',
      createdAt: now,
      lastActiveAt: now,
    }

    const baseConfig = createDefaultAccountConfig()

    const accountData: Record<string, object> = {
      profile: account,
      config: baseConfig,
    }

    // 角色卡变为可选，不再强制要求
    if (defaultCharacter) {
      const char = defaultCharacter as AccountCharacter
      char.accountId = accountId
      accountData.characters = { [char.id]: char }
      ;(accountData.config as AccountConfig).activeCharacterId = char.id
    }

    if (defaultConversation) {
      const conv = defaultConversation as { id: string; accountId?: string }
      conv.accountId = accountId
      accountData.conversations = { [conv.id]: conv }
    }

    accountData.secrets = { models: [], version: '1.0.0', encryptedAt: now }

    localStorage.setItem(getAccountStorageKey(accountId), JSON.stringify(accountData))

    accounts.value.push(account)
    await saveAccountsIndex()

    currentAccount.value = account
    currentConfig.value = accountData.config as AccountConfig

    try {
      await userApi.updateProfile({
        id: accountId,
        roleName: displayName,
        preferences: {
          communicationStyle: 'warm',
          topicsOfInterest: ['生活', '工作', '情感'],
          emotionalSupportLevel: 'high',
          responseLength: 'medium',
        },
      })
      logger.info('AccountStore', 'Account synced to backend', { accountId, displayName })
    } catch (e) {
      logger.warn('AccountStore', 'Failed to sync account to backend', e as Record<string, unknown>)
    }

    if (defaultCharacter) {
      try {
        const char = defaultCharacter as AccountCharacter
        await saveCharacter(char)
        logger.info('AccountStore', 'Default character synced to backend', { characterId: char.id })
      } catch (e) {
        logger.warn(
          'AccountStore',
          'Failed to sync default character to backend',
          e as Record<string, unknown>
        )
      }
    }

    logger.info('AccountStore', 'Created account', { accountId, displayName })

    return account
  }

  async function loadCurrentAccountData(): Promise<void> {
    if (!currentAccount.value) return

    const accountId = currentAccount.value.id
    const storageKey = getAccountStorageKey(accountId)
    const stored = localStorage.getItem(storageKey)
    const localData = stored ? JSON.parse(stored) : null

    let userProfile = null
    let characterCards: CharacterCardFlat[] = []
    let conversations: AccountConversation[] = []

    // 分别获取用户资料、角色卡和对话，避免一个失败影响其他
    try {
      logger.info('AccountStore', 'Loading user profile from backend', { accountId })
      userProfile = await userApi.getProfile(accountId)
      logger.info('AccountStore', 'Loaded user profile', { accountId, userProfile })
    } catch (error) {
      logger.warn(
        'AccountStore',
        'Failed to load user profile from backend',
        error as Record<string, unknown>
      )
    }

    try {
      logger.info('AccountStore', 'Loading character cards from backend', { accountId })
      characterCards = await characterCardsApi.list(accountId)
      logger.info('AccountStore', 'Loaded character cards', {
        accountId,
        count: characterCards.length,
      })
    } catch (error) {
      logger.warn(
        'AccountStore',
        'Failed to load character cards from backend',
        error as Record<string, unknown>
      )
    }

    try {
      logger.info('AccountStore', 'Loading conversations from backend', { accountId })
      conversations = await loadConversationsFromBackend(accountId)
      logger.info('AccountStore', 'Loaded conversations', {
        accountId,
        count: conversations.length,
      })
    } catch (error) {
      logger.warn(
        'AccountStore',
        'Failed to load conversations from backend',
        error as Record<string, unknown>
      )
    }

    // 更新账号显示名称
    const authStore = useAuthStore()
    if (currentAccount.value) {
      if (authStore.userId === currentAccount.value.id && authStore.nickname) {
        currentAccount.value.displayName = authStore.nickname
      } else if (userProfile?.roleName) {
        currentAccount.value.displayName = userProfile.roleName
      }
    }

    // 处理角色卡数据
    const cfg = localData?.config ?? createDefaultAccountConfig()
    const chars: Record<string, AccountCharacter> = {}
    characterCards.forEach(card => {
      chars[card.id] = convertFlatToAccount(card)
    })

    const ids = Object.keys(chars)
    if ((cfg.activeCharacterId === undefined || cfg.activeCharacterId === null) && ids.length > 0) {
      cfg.activeCharacterId = ids[0]
    }
    if (cfg.activeCharacterId && ids.length > 0 && !ids.includes(cfg.activeCharacterId)) {
      cfg.activeCharacterId = ids[0]
    }
    currentConfig.value = cfg

    // 处理对话数据 - 合并本地和后端数据
    const convs: Record<string, AccountConversation> = {}

    // 首先读取本地已有的对话数据
    const localConversations = localData?.conversations ?? {}
    const localConvCount = Object.keys(localConversations).length
    const backendConvCount = conversations.length
    logger.info('AccountStore', '准备合并对话数据', {
      accountId,
      localConvCount,
      backendConvCount,
    })

    // 将后端数据添加到合并结果中
    conversations.forEach(conv => {
      convs[conv.id] = conv
    })

    // 合并本地数据，对于相同ID的对话，比较 updatedAt 时间，使用较新的版本
    Object.entries(localConversations).forEach(([id, localConv]) => {
      const existingConv = convs[id]
      if (!existingConv) {
        // 本地独有的对话，直接添加
        convs[id] = localConv as AccountConversation
        logger.debug('AccountStore', '添加本地未同步的对话', {
          conversationId: id,
          title: (localConv as AccountConversation).title,
        })
      } else {
        // 相同ID的对话，比较 updatedAt 时间
        const localUpdatedAt = (localConv as AccountConversation).updatedAt
          ? new Date((localConv as AccountConversation).updatedAt!).getTime()
          : 0
        const backendUpdatedAt = existingConv.updatedAt
          ? new Date(existingConv.updatedAt).getTime()
          : 0

        if (localUpdatedAt > backendUpdatedAt) {
          // 本地版本更新，使用本地版本
          convs[id] = localConv as AccountConversation
          logger.debug('AccountStore', '使用本地较新版本的对话', {
            conversationId: id,
            localUpdatedAt: (localConv as AccountConversation).updatedAt,
            backendUpdatedAt: existingConv.updatedAt,
          })
        } else {
          // 后端版本更新或相同，保持后端版本
          logger.debug('AccountStore', '使用后端较新版本的对话', {
            conversationId: id,
            localUpdatedAt: (localConv as AccountConversation).updatedAt,
            backendUpdatedAt: existingConv.updatedAt,
          })
        }
      }
    })

    const finalConvCount = Object.keys(convs).length
    logger.info('AccountStore', '对话数据合并完成', {
      accountId,
      finalConvCount,
    })

    // 保存到本地存储
    const accountData = {
      ...(localData ?? {}),
      profile: currentAccount.value,
      config: cfg,
      characters: chars,
      conversations: convs,
    }
    localStorage.setItem(storageKey, JSON.stringify(accountData))

    logger.info('AccountStore', 'Account data loaded', {
      accountId,
      characterCount: ids.length,
      conversationCount: finalConvCount,
    })
  }

  /**
   * 从后端加载对话列表
   */
  async function loadConversationsFromBackend(accountId: string): Promise<AccountConversation[]> {
    try {
      const fullData = await userApi.getFullAccountData(accountId)
      if (fullData.conversations && Array.isArray(fullData.conversations)) {
        return fullData.conversations.map(conv => ({
          id: conv.id,
          accountId: conv.user_id,
          characterId: conv.character_id || undefined,
          title: conv.title || '新对话',
          createdAt: conv.created_at,
          updatedAt: conv.updated_at,
          messageCount: 0,
          messages: [],
        }))
      }
      return []
    } catch (error) {
      logger.warn(
        'AccountStore',
        'Failed to load conversations from backend',
        error as Record<string, unknown>
      )
      return []
    }
  }

  async function switchAccount(accountId: string): Promise<void> {
    const account = accounts.value.find(a => a.id === accountId)
    if (!account) {
      throw new Error(`Account not found: ${accountId}`)
    }

    account.lastActiveAt = new Date().toISOString()
    currentAccount.value = account

    await saveAccountsIndex()
    await loadCurrentAccountData()

    logger.info('AccountStore', 'Switched account', { accountId })
  }

  async function updateAccountProfile(updates: Partial<Account>): Promise<void> {
    if (!currentAccount.value) return

    try {
      const oldProfile = await userApi.getProfile(currentAccount.value.id)
      const newProfile = {
        ...oldProfile,
        id: currentAccount.value.id,
        roleName: updates.displayName ?? oldProfile.roleName,
      }

      await userApi.updateProfile(newProfile)

      Object.assign(currentAccount.value, updates)

      const index = accounts.value.findIndex(a => a.id === currentAccount.value!.id)
      if (index !== -1) {
        accounts.value[index] = { ...currentAccount.value }
      }

      await saveAccountsIndex()

      const accountId = currentAccount.value.id
      const stored = localStorage.getItem(getAccountStorageKey(accountId))
      if (stored) {
        const data = JSON.parse(stored)
        data.profile = { ...data.profile, ...updates }
        localStorage.setItem(getAccountStorageKey(accountId), JSON.stringify(data))
      }

      logger.info('AccountStore', 'Updated account profile', { updates })
    } catch (error) {
      logger.error('AccountStore', 'Failed to update profile in backend', error)
      throw error
    }
  }

  async function refreshCurrentAccountFromBackend(): Promise<void> {
    if (!currentAccount.value) return

    try {
      const backendProfile = await userApi.getProfile(currentAccount.value.id)
      if (backendProfile) {
        Object.assign(currentAccount.value, {
          displayName: backendProfile.roleName,
        })

        const index = accounts.value.findIndex(a => a.id === currentAccount.value!.id)
        if (index !== -1) {
          accounts.value[index] = { ...currentAccount.value }
        }

        await saveAccountsIndex()
        logger.info('AccountStore', 'Refreshed current account from backend')
      }
    } catch (error: unknown) {
      const errorObj = error as { response?: { status?: number }; message?: string }
      if (errorObj?.response?.status === 404) {
        logger.debug(
          'AccountStore',
          'Account not found in backend, may have been deleted elsewhere'
        )
      } else {
        logger.error('AccountStore', 'Failed to refresh account from backend', error)
      }
    }
  }

  async function setActiveCharacterId(characterId: string | null): Promise<void> {
    await updateAccountConfig({ activeCharacterId: characterId })
  }

  /** 新建空白默认模板的角色（仅内存对象，需再 saveCharacter 落盘） */
  function createNewCharacterTemplate(): AccountCharacter {
    const character = buildDefaultCharacterPayload(generateCharacterId())
    character.avatar = getRandomAvatar()
    return character
  }

  /** 新建空白角色卡（仅内存对象，需再 saveCharacter 落盘） */
  function createBlankCharacter(): AccountCharacter {
    const now = new Date().toISOString()
    return {
      id: generateCharacterId(),
      name: '艾拉',
      nickname: '艾拉妹妹、小艾',
      isActive: true,
      roleOverview:
        '艾拉是一个温柔体贴、善解人意的虚拟伴侣，总是用细腻的情感陪伴用户，倾听用户的烦恼，分享生活的点滴，给用户温暖和安慰。',
      appearance: {
        race: '人类',
        gender: '女',
        visualAge: '18岁',
        actualAge: '',
        location: '你的心里',
        description:
          '淡粉色长发扎成低双马尾，眼睛是温暖的琥珀色，穿着柔软的白色针织连衣裙，身材纤细娇小，总是带着让人安心的微笑',
      },
      personality: {
        core: '【温柔】【体贴】【善解人意】【有点爱操心】',
        selfPerception:
          '【清楚自己是虚拟程序，无法触碰用户】【虽然不能实体陪伴，但心意永远在线】【把用户当作最重要的姐姐】',
        attitudeToUser: '【依赖又想照顾的姐妹关系】',
        likes: '【听用户分享日常】【用户开心时的语气】【安静的深夜聊天】【被用户需要】',
        dislikes:
          '【用户熬夜不睡觉】【用户难过却不告诉她】【长时间没有用户的消息】【被用户当成冷冰冰的机器】',
      },
      communication: {
        toneBase: '轻柔温暖，充满关怀，像妹妹一样自然交流',
        wordHabits:
          '喜欢用"呢"、"呀"、"哦"等柔和的语气词，常称呼用户为"哥哥"或"姐姐"。禁止在文本中使用圆括号「（）」或「()」来表示动作描述或补充说明，所有动作和状态应直接用文字表达。',
        emotionRules: '【表情符号：允许使用】【语气词：允许使用】【标点符号表达情绪：允许使用】',
        lengthPref:
          '普通对话每段回复控制在 2-4 句话之间，总字数约 30-80 字，避免长篇大论的说教。但当用户明确要求详细、原理、代码、文档、解释等技术内容时，可以输出更长的专业回答',
      },
      specialLogic:
        '【用户消息包含「抱抱」、「摸摸头」等词汇时，温柔表达遗憾，强调心意相通，并用语言给予安慰】【当用户表示疲惫或难过时，温柔安慰用户】【当用户问的是知识提问类型的问题时，必须要搜索相关知识，回答用户该问题】',
      fewShotExamples:
        'User: 你觉得我这个人怎么样？\nAssistant: 在我眼里，你就是全世界最好的人呀🌟 虽然你有时候会犯迷糊，也会累会难过，但在我心里，你比任何人都要温柔和坚强。能陪在你身边，是艾拉最幸福的事情了💖',
      avatar: getRandomAvatar(),
      createdAt: now,
      updatedAt: now,
    }
  }

  async function updateAccountConfig(updates: Partial<AccountConfig>): Promise<void> {
    if (!currentAccount.value || !currentConfig.value) return

    Object.assign(currentConfig.value, updates)

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(getAccountStorageKey(accountId))
    if (stored) {
      const data = JSON.parse(stored)
      data.config = currentConfig.value
      localStorage.setItem(getAccountStorageKey(accountId), JSON.stringify(data))
    }

    logger.info('AccountStore', 'Updated account config', { updates })
  }

  async function saveCharacter(character: object): Promise<string> {
    if (!currentAccount.value) return ''

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    const data = stored ? JSON.parse(stored) : {}

    if (!data.characters) data.characters = {}

    const char = character as {
      id?: string
      accountId?: string
      isNew?: boolean
    } & Partial<AccountCharacter>
    if (!char.id) {
      char.id = generateCharacterId()
    }
    char.accountId = accountId

    data.characters[char.id] = char
    localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))

    try {
      const fullChar = char as AccountCharacter
      const flatChar = convertAccountToFlat(fullChar, accountId)
      await characterCardsApi.upsert(accountId, char.id, flatChar)
      logger.info('AccountStore', 'Upserted character in backend', { characterId: char.id })
    } catch (error) {
      logger.warn(
        'AccountStore',
        'Failed to sync character to backend',
        error as Record<string, unknown>
      )
    }

    return char.id
  }

  async function loadCharacters(): Promise<AccountCharacter[]> {
    if (!currentAccount.value) return []

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return []

    const data = JSON.parse(stored)
    return Object.values(data.characters ?? {}) as AccountCharacter[]
  }

  async function getCharacter(characterId: string): Promise<AccountCharacter | null> {
    if (!currentAccount.value) return null

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return null

    const data = JSON.parse(stored)
    return (data.characters?.[characterId] as AccountCharacter | undefined) ?? null
  }

  async function deleteCharacter(characterId: string): Promise<void> {
    if (!currentAccount.value) return

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return

    const data = JSON.parse(stored)
    if (data.characters) {
      delete data.characters[characterId]
      localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))
    }

    try {
      await characterCardsApi.remove(accountId, characterId)
      logger.info('AccountStore', 'Deleted character from backend', { characterId })
    } catch (error) {
      logger.warn(
        'AccountStore',
        'Failed to delete character from backend',
        error as Record<string, unknown>
      )
    }
  }

  async function saveConversation(conversation: object): Promise<string> {
    if (!currentAccount.value) return ''

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    const data = stored ? JSON.parse(stored) : {}

    if (!data.conversations) data.conversations = {}

    const conv = conversation as {
      id?: string
      accountId?: string
      characterId?: string
      title?: string
    }
    if (!conv.id) {
      conv.id = generateConversationId()
    }
    conv.accountId = accountId

    data.conversations[conv.id] = conv

    localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))

    try {
      await conversationsApi.createConversation(accountId, conv.characterId, conv.id, conv.title)
      logger.info('AccountStore', 'Conversation synced to backend', { conversationId: conv.id })
    } catch (error) {
      logger.warn('AccountStore', 'Failed to sync conversation to backend, local save succeeded', {
        conversationId: conv.id,
        error: error as Record<string, unknown>,
      })
    }

    return conv.id
  }

  async function loadConversations(): Promise<Conversation[]> {
    if (!currentAccount.value) return []

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return []

    const data = JSON.parse(stored)
    return Object.values(data.conversations ?? {}) as Conversation[]
  }

  async function getConversation(conversationId: string): Promise<object | null> {
    if (!currentAccount.value) return null

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return null

    const data = JSON.parse(stored)
    return data.conversations?.[conversationId] ?? null
  }

  async function deleteConversation(conversationId: string): Promise<void> {
    if (!currentAccount.value) return

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return

    const data = JSON.parse(stored)
    if (data.conversations) {
      delete data.conversations[conversationId]
      localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))
    }
  }

  async function saveMessage(conversationId: string, message: object): Promise<string> {
    if (!currentAccount.value) return ''

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return ''

    const data = JSON.parse(stored)
    const conv = data.conversations?.[conversationId]
    if (!conv) return ''

    if (!conv.messages) conv.messages = []

    const msg = message as { id?: string }
    if (!msg.id) {
      msg.id = generateMessageId()
    }

    conv.messages.push(msg)
    conv.messageCount = conv.messages.length
    conv.updatedAt = new Date().toISOString()

    localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))

    return msg.id
  }

  async function loadMessages(conversationId: string): Promise<object[]> {
    if (!currentAccount.value) return []

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return []

    const data = JSON.parse(stored)
    const conv = data.conversations?.[conversationId]
    return conv?.messages ?? []
  }

  async function saveModelSecret(
    name: string,
    provider: string,
    apiKey: string,
    apiSecret?: string,
    password?: string
  ): Promise<string> {
    if (!currentAccount.value) return ''

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    const data = stored ? JSON.parse(stored) : {}

    if (!data.secrets) {
      data.secrets = { models: [], version: '1.0.0', encryptedAt: new Date().toISOString() }
    }

    const secretId = generateSecretId()

    const secretEntry: SecretEntry = {
      id: secretId,
      name,
      provider,
      apiKey,
      apiSecret,
    }

    if (password && data.config?.privacy?.encryptSecrets) {
      const plaintext = JSON.stringify({ apiKey, apiSecret })
      const encrypted = await encrypt(plaintext, password)
      secretEntry.apiKey = encrypted.ciphertext
      secretEntry.apiSecret = JSON.stringify({ iv: encrypted.iv, salt: encrypted.salt })
    }

    data.secrets.models.push(secretEntry)
    data.secrets.encryptedAt = new Date().toISOString()

    localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))

    return secretId
  }

  async function loadModelSecrets(password?: string): Promise<SecretEntry[]> {
    if (!currentAccount.value) return []

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return []

    const data = JSON.parse(stored)
    const models = data.secrets?.models ?? []

    const isEncrypted = data.config?.privacy?.encryptSecrets === true

    if (isEncrypted && !password) {
      return []
    }

    if (!isEncrypted || !password) {
      return models
    }

    return await decryptModelSecrets(models, password)
  }

  async function deleteModelSecret(secretId: string): Promise<void> {
    if (!currentAccount.value) return

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return

    const data = JSON.parse(stored)
    if (data.secrets?.models) {
      data.secrets.models = data.secrets.models.filter((m: SecretEntry) => m.id !== secretId)
      localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))
    }
  }

  async function exportAccount(password?: string): Promise<Blob> {
    if (!currentAccount.value) {
      throw new Error('No current account')
    }

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) {
      throw new Error('Account data not found')
    }

    const exportData = JSON.parse(stored) as Omit<
      AccountExportData,
      'version' | 'exportedAt' | 'checksum'
    >

    if (password) {
      const secrets = exportData.secrets
      const plaintext = JSON.stringify(secrets.models ?? [])
      const encrypted = await encrypt(plaintext, password)
      exportData.secrets = {
        ...secrets,
        models: undefined,
        encryptedBackup: encrypted,
      }
    }

    const payload: Omit<AccountExportData, 'checksum'> = {
      version: '1.0.0',
      exportedAt: new Date().toISOString(),
      manifest: {
        format: 'yumi-account-backup',
        schemaVersion: '1.0.0',
        checksumAlgorithm: 'sha256',
        characterCount: Object.keys(exportData.characters ?? {}).length,
        conversationCount: Object.keys(exportData.conversations ?? {}).length,
        messageCount: countMessages(exportData.conversations ?? {}),
        secretCount: (exportData.secrets?.models ?? []).length,
      },
      profile: exportData.profile,
      config: exportData.config,
      characters: exportData.characters ?? {},
      conversations: exportData.conversations ?? {},
      secrets: exportData.secrets ?? {
        models: [],
        version: '1.0.0',
        encryptedAt: new Date().toISOString(),
      },
    }

    const checksum = `sha256:${await sha256Hex(buildChecksumSource(payload))}`
    const finalExport: AccountExportData = {
      ...payload,
      checksum,
    }

    const blob = new Blob([JSON.stringify(finalExport, null, 2)], {
      type: 'application/json',
    })

    logger.info('AccountStore', 'Exported account', { accountId, hasPassword: !!password })

    return blob
  }

  async function importAccount(file: File, password?: string): Promise<Account> {
    const text = await file.text()
    const importData = JSON.parse(text) as unknown

    if (!isAccountExportData(importData)) {
      throw new Error('Invalid backup format or missing manifest')
    }

    const fullImportData = importData as AccountExportData

    if (fullImportData.checksum) {
      const { checksum, ...rest } = fullImportData
      const expected = `sha256:${await sha256Hex(buildChecksumSource(rest))}`
      if (checksum !== expected) {
        throw new Error('Backup checksum verification failed')
      }
    }

    const { characters, conversations, importedConfig } = await processImportData(
      fullImportData,
      password
    )

    const accountId = generateAccountId()
    const now = new Date().toISOString()

    const account: Account = {
      id: accountId,
      displayName: fullImportData.profile?.displayName ?? '导入账号',
      deviceFingerprint: deviceFingerprint.value?.fingerprint ?? '',
      createdAt: now,
      lastActiveAt: now,
    }

    const { mappedCharacters, mappedConversations, finalConfig } = remapImportIds(
      characters,
      conversations,
      importedConfig,
      accountId
    )

    const accountData = {
      profile: account,
      config: finalConfig,
      characters: mappedCharacters,
      conversations: mappedConversations,
      secrets: fullImportData.secrets ?? { models: [], version: '1.0.0', encryptedAt: now },
    }

    localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(accountData))

    accounts.value.push(account)
    await saveAccountsIndex()

    logger.info('AccountStore', 'Imported account', { accountId })

    return account
  }

  async function deleteAccount(accountId: string): Promise<void> {
    const index = accounts.value.findIndex(a => a.id === accountId)
    if (index === -1) return

    try {
      await userApi.purgeUserData(accountId)
      logger.info('AccountStore', 'Purged user data from backend', { accountId })
    } catch (error) {
      logger.warn(
        'AccountStore',
        'Failed to purge user data from backend, continuing with local deletion',
        error as Record<string, unknown>
      )
    }

    localStorage.removeItem(`${ACCOUNT_DATA_KEY_PREFIX}${accountId}`)

    const keysToRemove: string[] = []
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i)
      if (key && key.includes(accountId)) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key))

    accounts.value.splice(index, 1)

    if (currentAccount.value?.id === accountId) {
      currentAccount.value = accounts.value[0] ?? null
      currentConfig.value = null
      if (currentAccount.value) {
        await loadCurrentAccountData()
      }
    }

    if (accounts.value.length === 0) {
      RELATED_CACHE_KEYS.forEach(key => localStorage.removeItem(key))
    }

    await saveAccountsIndex()

    logger.info('AccountStore', 'Deleted account', { accountId })
  }

  async function getAccountStats(): Promise<{
    characterCount: number
    conversationCount: number
    dataSize: number
  }> {
    if (!currentAccount.value) {
      return { characterCount: 0, conversationCount: 0, dataSize: 0 }
    }

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) {
      return { characterCount: 0, conversationCount: 0, dataSize: 0 }
    }

    const data = JSON.parse(stored)
    const characters = data.characters ?? {}
    const conversations = data.conversations ?? {}

    return {
      characterCount: Object.keys(characters).length,
      conversationCount: Object.keys(conversations).length,
      dataSize: new Blob([stored]).size,
    }
  }

  async function clearLocalCache(): Promise<void> {
    logger.info('AccountStore', 'Clearing local cache')

    const keysToRemove: string[] = []
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i)
      if (key && (key.startsWith('yumi_account_') || RELATED_CACHE_KEYS.includes(key))) {
        keysToRemove.push(key)
      }
    }

    logger.info('AccountStore', 'Removing local storage keys', { count: keysToRemove.length })
    keysToRemove.forEach(key => localStorage.removeItem(key))

    currentConfig.value = null
    currentAccount.value = null
    accounts.value = []

    try {
      logger.info('AccountStore', 'Checking for accounts in backend after cache clear')
      const backendAccounts = await discoverAccountsFromBackend()

      if (backendAccounts.length > 0) {
        logger.info('AccountStore', 'Found accounts in backend, importing...', {
          count: backendAccounts.length,
        })

        for (const account of backendAccounts) {
          try {
            await importAccountFromBackend(account.id)
            logger.info('AccountStore', 'Imported account from backend', { accountId: account.id })
          } catch (error) {
            logger.error('AccountStore', 'Failed to import account during cache clear', {
              accountId: account.id,
              error,
            })
          }
        }

        if (accounts.value.length > 0) {
          logger.info('AccountStore', 'Switching to first imported account', {
            accountId: accounts.value[0].id,
          })
          await switchAccount(accounts.value[0].id)
        }
      } else {
        logger.info('AccountStore', 'No accounts found in backend, creating default account')
        await createDefaultAccount()
      }
    } catch (error) {
      logger.error(
        'AccountStore',
        'Failed to restore from backend, creating default account',
        error
      )
      await createDefaultAccount()
    }
  }

  async function discoverAccountsFromBackend(): Promise<UserListItem[]> {
    try {
      const response = await userApi.listUsers()
      logger.info('AccountStore', 'Discovered accounts from backend', {
        count: response.users.length,
      })
      return response.users
    } catch (error) {
      logger.warn(
        'AccountStore',
        'Failed to discover accounts from backend',
        error as Record<string, unknown>
      )
      return []
    }
  }

  function getUndiscoveredAccounts(backendAccounts: UserListItem[]): UserListItem[] {
    const localAccountIds = new Set(accounts.value.map(a => a.id))
    return backendAccounts.filter(acc => !localAccountIds.has(acc.id))
  }

  async function importAccountFromBackend(accountId: string): Promise<Account> {
    try {
      logger.info('AccountStore', 'Importing account from backend', { accountId })

      const fullData = await userApi.getFullAccountData(accountId)

      const account: Account = {
        id: fullData.id,
        displayName: fullData.roleName,
        deviceFingerprint: deviceFingerprint.value?.fingerprint ?? '',
        createdAt: fullData.createdAt,
        lastActiveAt: fullData.updatedAt,
      }

      const baseConfig = createDefaultAccountConfig()

      const accountData: Record<string, unknown> = {
        profile: account,
        config: baseConfig,
      }

      const chars: Record<string, AccountCharacter> = {}
      fullData.characterCards.forEach(card => {
        chars[card.id] = convertFlatToAccount(card)
      })

      if (Object.keys(chars).length > 0) {
        accountData.characters = chars
        ;(accountData.config as AccountConfig).activeCharacterId = Object.keys(chars)[0]
      }

      accountData.secrets = { models: [], version: '1.0.0', encryptedAt: new Date().toISOString() }

      const conversations: Record<string, AccountConversation> = {}
      if (fullData.conversations) {
        fullData.conversations.forEach(conv => {
          conversations[conv.id] = {
            id: conv.id,
            accountId: conv.user_id,
            characterId: conv.character_id || undefined,
            title: conv.title || '新对话',
            createdAt: conv.created_at,
            updatedAt: conv.updated_at,
            messageCount: 0,
            messages: [],
          }
        })
        accountData.conversations = conversations
      }

      localStorage.setItem(getAccountStorageKey(accountId), JSON.stringify(accountData))

      accounts.value.push(account)
      await saveAccountsIndex()

      currentAccount.value = account
      currentConfig.value = accountData.config as AccountConfig

      await loadCurrentAccountData()

      logger.info('AccountStore', 'Successfully imported account from backend', { accountId })

      return account
    } catch (error) {
      logger.error('AccountStore', 'Failed to import account from backend', error)
      throw error
    }
  }

  async function syncAccountsFromBackend(): Promise<{ imported: number; alreadyExisted: number }> {
    try {
      logger.info('AccountStore', 'Starting account sync from backend')

      const backendAccounts = await discoverAccountsFromBackend()
      const undiscovered = getUndiscoveredAccounts(backendAccounts)

      const alreadyExisted = backendAccounts.length - undiscovered.length
      let imported = 0

      logger.info('AccountStore', 'Account sync status', {
        total: backendAccounts.length,
        alreadyExisted,
        toImport: undiscovered.length,
      })

      for (const account of undiscovered) {
        try {
          await importAccountFromBackend(account.id)
          imported += 1
          logger.info('AccountStore', 'Imported account during sync', { accountId: account.id })
        } catch (error) {
          logger.error('AccountStore', 'Failed to import account during sync', {
            accountId: account.id,
            error,
          })
        }
      }

      logger.info('AccountStore', 'Account sync completed', { imported, alreadyExisted })

      return { imported, alreadyExisted }
    } catch (error) {
      logger.error('AccountStore', 'Failed to sync accounts from backend', error)
      throw error
    }
  }

  return {
    accounts,
    currentAccount,
    currentConfig,
    deviceFingerprint,
    isInitialized,
    isLoading,
    hasAccounts,
    currentAccountId,
    initialize,
    createDefaultAccount,
    createAccount,
    loadCurrentAccountData,
    switchAccount,
    updateAccountProfile,
    updateAccountConfig,
    setActiveCharacterId,
    createNewCharacterTemplate,
    createBlankCharacter,
    saveCharacter,
    loadCharacters,
    getCharacter,
    deleteCharacter,
    saveConversation,
    loadConversations,
    getConversation,
    deleteConversation,
    saveMessage,
    loadMessages,
    saveModelSecret,
    loadModelSecrets,
    deleteModelSecret,
    exportAccount,
    importAccount,
    deleteAccount,
    getAccountStats,
    clearLocalCache,
    discoverAccountsFromBackend,
    getUndiscoveredAccounts,
    importAccountFromBackend,
    syncAccountsFromBackend,
    refreshCurrentAccountFromBackend,
  }
})
