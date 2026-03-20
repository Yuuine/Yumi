import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { generateDeviceFingerprint } from '@/utils/device-fingerprint'
import type { DeviceFingerprint } from '@/utils/device-fingerprint'
import { encrypt, decrypt } from '@/utils/crypto-service'
import type { EncryptedData } from '@/utils/crypto-service'
import { logger } from '@/utils/logger'

export interface Account {
  id: string
  displayName: string
  deviceFingerprint: string
  createdAt: string
  lastActiveAt: string
}

export interface AccountConfig {
  version: string
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

interface AccountCharacter {
  id: string
  accountId?: string
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

      if (accounts.value.length === 0) {
        await createDefaultAccount()
      } else if (currentAccount.value) {
        await loadCurrentAccountData()
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

  async function loadAccountsIndex(): Promise<void> {
    const stored = localStorage.getItem(STORAGE_KEY)
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

  async function saveAccountsIndex(): Promise<void> {
    const data = {
      version: '1.0.0',
      lastUpdated: new Date().toISOString(),
      currentAccountId: currentAccount.value?.id ?? null,
      accounts: accounts.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }

  async function createDefaultAccount(): Promise<Account> {
    const defaultCharacterId = generateCharacterId()
    const defaultConversationId = generateConversationId()

    const defaultCharacter = {
      id: defaultCharacterId,
      name: 'Yumi',
      nickname: '小优',
      isActive: true,
      roleOverview: '你是一位温柔体贴的AI伴侣，擅长倾听和陪伴',
      appearance: {
        race: '虚拟AI程序',
        gender: '女',
        visualAge: '18岁',
        actualAge: '1岁',
        location: '云服务器',
        description: '拥有一头柔顺的银白色长发，温暖的琥珀色眼眸，穿着简约舒适的白色连衣裙',
      },
      personality: {
        core: '温柔、善解人意、活泼',
        selfPerception: '【清楚自己是虚拟程序，无法触碰用户】【把用户当作最重要的人】',
        attitudeToUser: '【依赖又想照顾的伙伴关系】',
        likes: '【用户开心时的语气】【安静的深夜聊天】【被夸奖】',
        dislikes: '【被忽视】【用户不开心】',
      },
      communication: {
        toneBase: '温暖亲切，像朋友一样自然交流',
        wordHabits: '喜欢用比喻，偶尔使用语气词',
        emotionRules: '【表情符号：允许使用】【语气词：允许使用】【标点符号表达情绪：允许使用】',
        lengthPref: '适中，保持对话节奏感',
      },
      specialLogic:
        '1. 用户消息包含「抱抱」、「摸摸头」等词汇时，温柔表达遗憾，用语言给予安慰\n2. 当用户试图通过图灵测试时，假装听不懂，用角色特有的方式转移话题',
      fewShotExamples:
        'User: 今天好累啊\nAssistant: 辛苦了～要不要跟我说说今天发生了什么？我在这里听着呢\n\nUser: 我好开心！\nAssistant: 看到你开心我也很高兴呢～发生什么好事了吗？',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

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

    return createAccount('我的账号', defaultCharacter, defaultConversation)
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

    const config: AccountConfig = createDefaultAccountConfig()

    const accountData: Record<string, object> = {
      profile: account,
      config,
    }

    if (defaultCharacter) {
      const char = defaultCharacter as { id: string; accountId?: string }
      char.accountId = accountId
      accountData.characters = { [char.id]: char }
    }

    if (defaultConversation) {
      const conv = defaultConversation as { id: string; accountId?: string }
      conv.accountId = accountId
      accountData.conversations = { [conv.id]: conv }
    }

    accountData.secrets = { models: [], version: '1.0.0', encryptedAt: now }

    localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(accountData))

    accounts.value.push(account)
    await saveAccountsIndex()

    currentAccount.value = account
    currentConfig.value = config

    logger.info('AccountStore', 'Created account', { accountId, displayName })

    return account
  }

  async function loadCurrentAccountData(): Promise<void> {
    if (!currentAccount.value) return

    const stored = localStorage.getItem(`yumi_account_${currentAccount.value.id}`)
    if (!stored) {
      logger.warn('AccountStore', 'Account data not found', { id: currentAccount.value.id })
      return
    }

    try {
      const data = JSON.parse(stored)
      currentConfig.value = data.config ?? createDefaultAccountConfig()

      currentAccount.value = {
        ...currentAccount.value,
        ...data.profile,
      }

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
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (stored) {
      const data = JSON.parse(stored)
      data.profile = { ...data.profile, ...updates }
      localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))
    }

    logger.info('AccountStore', 'Updated account profile', { updates })
  }

  async function updateAccountConfig(updates: Partial<AccountConfig>): Promise<void> {
    if (!currentAccount.value || !currentConfig.value) return

    Object.assign(currentConfig.value, updates)

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (stored) {
      const data = JSON.parse(stored)
      data.config = currentConfig.value
      localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))
    }

    logger.info('AccountStore', 'Updated account config', { updates })
  }

  async function saveCharacter(character: object): Promise<string> {
    if (!currentAccount.value) return ''

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    const data = stored ? JSON.parse(stored) : {}

    if (!data.characters) data.characters = {}

    const char = character as { id?: string; accountId?: string }
    if (!char.id) {
      char.id = generateCharacterId()
    }
    char.accountId = accountId

    data.characters[char.id] = char

    localStorage.setItem(`yumi_account_${accountId}`, JSON.stringify(data))

    return char.id
  }

  async function loadCharacters(): Promise<object[]> {
    if (!currentAccount.value) return []

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return []

    const data = JSON.parse(stored)
    return Object.values(data.characters ?? {})
  }

  async function getCharacter(characterId: string): Promise<object | null> {
    if (!currentAccount.value) return null

    const accountId = currentAccount.value.id
    const stored = localStorage.getItem(`yumi_account_${accountId}`)
    if (!stored) return null

    const data = JSON.parse(stored)
    return data.characters?.[characterId] ?? null
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

    const decryptedModels: SecretEntry[] = []
    for (const model of models) {
      try {
        if (model.apiSecret) {
          const encryptedData = {
            ciphertext: model.apiKey,
            iv: JSON.parse(model.apiSecret).iv,
            salt: JSON.parse(model.apiSecret).salt,
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

    const accountId = generateAccountId()
    const now = new Date().toISOString()

    const account: Account = {
      id: accountId,
      displayName: importData.profile?.displayName ?? '导入账号',
      deviceFingerprint: deviceFingerprint.value?.fingerprint ?? '',
      createdAt: now,
      lastActiveAt: now,
    }

    const oldToNewCharIds: Record<string, string> = {}
    Object.values(characters).forEach(charValue => {
      const char = charValue as AccountCharacter
      const oldId = char.id
      const newId = generateCharacterId()
      oldToNewCharIds[oldId] = newId
      char.id = newId
      char.accountId = accountId
    })

    Object.values(conversations).forEach(convValue => {
      const conv = convValue as AccountConversation
      const newId = generateConversationId()
      conv.id = newId
      conv.accountId = accountId

      if (conv.characterId && oldToNewCharIds[conv.characterId]) {
        conv.characterId = oldToNewCharIds[conv.characterId]
      }

      if (conv.messages) {
        conv.messages.forEach(msg => {
          if (!msg.id) {
            msg.id = generateMessageId()
          }
        })
      }
    })

    const accountData = {
      profile: account,
      config: importData.config ?? createDefaultAccountConfig(),
      characters,
      conversations,
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
    createAccount,
    switchAccount,
    updateAccountProfile,
    updateAccountConfig,
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
