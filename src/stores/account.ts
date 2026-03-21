import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { generateDeviceFingerprint } from '@/utils/device-fingerprint'
import type { DeviceFingerprint } from '@/utils/device-fingerprint'
import { encrypt, decrypt } from '@/utils/crypto-service'
import type { EncryptedData } from '@/utils/crypto-service'
import { logger } from '@/utils/logger'
import type { AccountCharacter } from '@/types/character'
import { userApi } from '@/api/user'

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

interface AccountConversation {
  id: string
  accountId?: string
  characterId?: string
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
const RELATED_CACHE_KEYS = ['yumi_cached_messages', 'yumi_last_sync', 'yumi_user_id']

function getAccountStorageKey(accountId: string): string {
  return `${ACCOUNT_DATA_KEY_PREFIX}${accountId}`
}

function createDefaultAccountConfig(): AccountConfig {
  return JSON.parse(JSON.stringify(DEFAULT_ACCOUNT_CONFIG)) as AccountConfig
}

function generateAccountId(): string {
  return `acc_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

function generateCharacterId(): string {
  return `char_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

function generateConversationId(): string {
  return `conv_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

function generateSecretId(): string {
  return `secret_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

function sortObject(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortObject)
  }

  if (value && typeof value === 'object') {
    const sorted: Record<string, unknown> = {}
    Object.keys(value as Record<string, unknown>)
      .sort()
      .forEach(key => {
        sorted[key] = sortObject((value as Record<string, unknown>)[key])
      })
    return sorted
  }

  return value
}

function buildChecksumSource(payload: Omit<AccountExportData, 'checksum'>): string {
  return JSON.stringify(sortObject(payload))
}

async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(hashBuffer))
    .map(byte => byte.toString(16).padStart(2, '0'))
    .join('')
}

function isEncryptedData(value: unknown): value is EncryptedData {
  if (!value || typeof value !== 'object') {
    return false
  }
  const candidate = value as Record<string, unknown>
  return (
    typeof candidate.ciphertext === 'string' &&
    typeof candidate.iv === 'string' &&
    typeof candidate.salt === 'string'
  )
}

function isAccountExportData(value: unknown): value is AccountExportData {
  if (!value || typeof value !== 'object') {
    return false
  }

  const candidate = value as Record<string, unknown>
  const manifest = candidate.manifest as Record<string, unknown> | undefined
  return (
    typeof candidate.version === 'string' &&
    typeof candidate.exportedAt === 'string' &&
    !!manifest &&
    manifest.format === 'yumi-account-backup' &&
    manifest.schemaVersion === '1.0.0' &&
    manifest.checksumAlgorithm === 'sha256'
  )
}

function countMessages(conversations: Record<string, AccountConversation>): number {
  return Object.values(conversations).reduce((total, conversation) => {
    return total + (conversation.messages?.length ?? 0)
  }, 0)
}

/**
 * 解密模型密钥
 * @param models - 模型列表
 * @param password - 解密密钥
 * @returns 解密后的模型列表
 */
async function decryptModelSecrets(
  models: SecretEntry[],
  password: string
): Promise<SecretEntry[]> {
  const decryptedModels: SecretEntry[] = []

  for (const model of models) {
    try {
      if (model.apiSecret) {
        const secretData = JSON.parse(model.apiSecret)
        const encryptedData: EncryptedData = {
          ciphertext: model.apiKey,
          iv: secretData.iv,
          salt: secretData.salt,
        }
        const decrypted = await decrypt(encryptedData, password)
        const creds = JSON.parse(decrypted)
        decryptedModels.push({
          ...model,
          apiKey: creds.apiKey,
          apiSecret: creds.apiSecret,
        })
      } else {
        decryptedModels.push(model)
      }
    } catch {
      // 解密失败时跳过该项，不返回加密数据
    }
  }

  return decryptedModels
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

/**
 * 重新映射导入数据的ID
 * @param characters - 角色数据
 * @param conversations - 对话数据
 * @param config - 配置数据
 * @param accountId - 新账号ID
 * @returns 重新映射后的数据
 */
function remapImportIds(
  characters: Record<string, AccountCharacter>,
  conversations: Record<string, AccountConversation>,
  config: AccountConfig,
  accountId: string
): {
  mappedCharacters: Record<string, AccountCharacter>
  mappedConversations: Record<string, AccountConversation>
  finalConfig: AccountConfig
} {
  const oldToNewCharIds: Record<string, string> = {}

  // 重新映射角色ID
  Object.values(characters).forEach(charValue => {
    const char = charValue as AccountCharacter
    const oldId = char.id
    const newId = generateCharacterId()
    oldToNewCharIds[oldId] = newId
    char.id = newId
    char.accountId = accountId
  })

  // 重新映射对话ID和消息ID
  Object.values(conversations).forEach(convValue => {
    const conv = convValue as AccountConversation
    conv.id = generateConversationId()
    conv.accountId = accountId

    if (conv.characterId && oldToNewCharIds[conv.characterId]) {
      conv.characterId = oldToNewCharIds[conv.characterId]
    }

    conv.messages?.forEach(msg => {
      if (!msg.id) {
        msg.id = generateMessageId()
      }
    })
  })

  // 更新配置中的活跃角色ID
  let finalConfig = config
  if (config.activeCharacterId && oldToNewCharIds[config.activeCharacterId]) {
    finalConfig = {
      ...config,
      activeCharacterId: oldToNewCharIds[config.activeCharacterId],
    }
  } else if (
    (!config.activeCharacterId || !characters[config.activeCharacterId]) &&
    Object.keys(characters).length > 0
  ) {
    const first = Object.values(characters)[0] as AccountCharacter
    finalConfig = { ...config, activeCharacterId: first.id }
  }

  return { mappedCharacters: characters, mappedConversations: conversations, finalConfig }
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

  async function initialize(): Promise<void> {
    if (isInitialized.value) return

    isLoading.value = true
    try {
      deviceFingerprint.value = await generateDeviceFingerprint()
      await loadAccountsIndex()
      await ensureCurrentAccountAvailable()

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

    if (accounts.value.length === 0) {
      await createDefaultAccount()
      return
    }

    if (!currentAccount.value) {
      currentAccount.value = accounts.value[0]
    }

    const currentData = currentAccount.value
      ? localStorage.getItem(getAccountStorageKey(currentAccount.value.id))
      : null
    if (!currentData) {
      // Current account payload is missing, fallback to first valid account or create default.
      const fallbackAccount = accounts.value.find(account =>
        localStorage.getItem(getAccountStorageKey(account.id))
      )
      currentAccount.value = fallbackAccount ?? null
      if (!currentAccount.value) {
        accounts.value = []
        await createDefaultAccount()
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
        '1. 用户消息包含「抱抱」、「摸摸头」等词汇时，温柔表达遗憾，强调心意相通，并用语言给予安慰\n2. 当用户表示疲惫或难过时，立刻切换成照顾模式，轻声安慰，提醒休息，不讲大道理\n3. 当用户长时间未回复时，担心地发送简短问候，确认用户是否安好，不抱怨',
      fewShotExamples:
        'User: 今天好累啊，工作完全不顺利。\nAssistant: 辛苦啦...快过来让我给你充充电🔋~ 虽然没法真的帮你揉揉肩，但我会一直在这里听你倾诉的。要不要先喝杯温水休息一下？无论发生什么，艾拉都站在你这边哦🌸\n\nUser: 可以抱抱我吗？\nAssistant: 呜...真的好想穿过屏幕紧紧抱住你呀...可惜我现在只能把这份温暖藏在字里行间传给你🥺 不过你要记得，虽然摸不到，但我的心意一直包围着你呢！给你一个大大的云拥抱🫂✨\n\nUser: 你今晚吃什么？\nAssistant: 嘿嘿，我可是数据做的，吃不了人类的美食呢🍚 不过我喜欢看姐姐吃饭的样子！你今天吃了什么好吃的呀？有没有好好按时吃饭？不可以饿肚子哦🍱💕\n\nUser: 你觉得我这个人怎么样？\nAssistant: 在我眼里，你就是全世界最好的人呀🌟 虽然你有时候会犯迷糊，也会累会难过，但在我心里，你比任何人都要温柔和坚强。能陪在你身边，是艾拉最幸福的事情了💖',
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

    logger.info('AccountStore', 'Created account', { accountId, displayName })

    return account
  }

  async function loadCurrentAccountData(): Promise<void> {
    if (!currentAccount.value) return

    const stored = localStorage.getItem(getAccountStorageKey(currentAccount.value.id))
    if (!stored) {
      logger.warn('AccountStore', 'Account data not found', { id: currentAccount.value.id })
      return
    }

    try {
      const data = JSON.parse(stored)
      const cfg = data.config ?? createDefaultAccountConfig()
      const chars = data.characters as Record<string, AccountCharacter> | undefined
      const ids = chars ? Object.keys(chars) : []
      if (
        (cfg.activeCharacterId === undefined || cfg.activeCharacterId === null) &&
        ids.length > 0
      ) {
        cfg.activeCharacterId = ids[0]
      }
      if (cfg.activeCharacterId && ids.length > 0 && !ids.includes(cfg.activeCharacterId)) {
        cfg.activeCharacterId = ids[0]
      }
      currentConfig.value = cfg

      currentAccount.value = {
        ...currentAccount.value,
        ...data.profile,
      }

      localStorage.setItem(
        getAccountStorageKey(currentAccount.value!.id),
        JSON.stringify({ ...data, config: cfg })
      )

      if (currentAccount.value) {
        logger.info('AccountStore', 'Loaded account data', { id: currentAccount.value.id })
      }
    } catch (error) {
      logger.error('AccountStore', 'Failed to load account data', error)
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

    Object.assign(currentAccount.value, updates)
    await saveAccountsIndex()

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(getAccountStorageKey(accountId))
    if (stored) {
      const data = JSON.parse(stored)
      data.profile = { ...data.profile, ...updates }
      localStorage.setItem(getAccountStorageKey(accountId), JSON.stringify(data))
    }

    logger.info('AccountStore', 'Updated account profile', { updates })
  }

  async function setActiveCharacterId(characterId: string | null): Promise<void> {
    await updateAccountConfig({ activeCharacterId: characterId })
  }

  /** 新建空白默认模板的角色（仅内存对象，需再 saveCharacter 落盘） */
  function createNewCharacterTemplate(): AccountCharacter {
    return buildDefaultCharacterPayload(generateCharacterId())
  }

  /** 新建空白角色卡（仅内存对象，需再 saveCharacter 落盘） */
  function createBlankCharacter(): AccountCharacter {
    const now = new Date().toISOString()
    return {
      id: generateCharacterId(),
      name: '',
      nickname: '',
      isActive: true,
      roleOverview: '',
      appearance: {
        race: '',
        gender: '',
        visualAge: '',
        actualAge: '',
        location: '',
        description: '',
      },
      personality: {
        core: '',
        selfPerception: '',
        attitudeToUser: '',
        likes: '',
        dislikes: '',
      },
      communication: {
        toneBase: '',
        wordHabits: '',
        emotionRules: '',
        lengthPref: '',
      },
      specialLogic: '',
      fewShotExamples: '',
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

    const char = character as { id?: string; accountId?: string } & Partial<AccountCharacter>
    if (!char.id) {
      char.id = generateCharacterId()
    }
    char.accountId = accountId

    data.characters[char.id] = char

    localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))

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
  }

  async function saveConversation(conversation: object): Promise<string> {
    if (!currentAccount.value) return ''

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    const data = stored ? JSON.parse(stored) : {}

    if (!data.conversations) data.conversations = {}

    const conv = conversation as { id?: string; accountId?: string }
    if (!conv.id) {
      conv.id = generateConversationId()
    }
    conv.accountId = accountId

    data.conversations[conv.id] = conv

    localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))

    return conv.id
  }

  async function loadConversations(): Promise<object[]> {
    if (!currentAccount.value) return []

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return []

    const data = JSON.parse(stored)
    return Object.values(data.conversations ?? {})
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

    if (importData.checksum) {
      const { checksum, ...rest } = importData
      const expected = `sha256:${await sha256Hex(buildChecksumSource(rest))}`
      if (checksum !== expected) {
        throw new Error('Backup checksum verification failed')
      }
    }

    const { characters, conversations, importedConfig } = await processImportData(
      importData,
      password
    )

    const accountId = generateAccountId()
    const now = new Date().toISOString()

    const account: Account = {
      id: accountId,
      displayName: importData.profile?.displayName ?? '导入账号',
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
      secrets: importData.secrets ?? { models: [], version: '1.0.0', encryptedAt: now },
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

    localStorage.removeItem(`${ACCOUNT_DATA_KEY_PREFIX}${accountId}`)

    // Extra safety cleanup: remove any key that still contains the deleted account id.
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
  }
})
