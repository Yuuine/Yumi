/**
 * 账户相关的工具函数
 * 从 stores/account.ts 中提取的纯工具函数
 */

import type { AccountCharacter } from '@/types/character'
import type { EncryptedData } from '@/utils/crypto-service'
import { decrypt } from '@/utils/crypto-service'
import type { SecretEntry } from '@/stores/account'

export function generateAccountId(): string {
  return `acc_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

export function generateCharacterId(): string {
  return `char_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

export function generateConversationId(): string {
  return `conv_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

export function generateSecretId(): string {
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

export function buildChecksumSource(payload: unknown): string {
  return JSON.stringify(sortObject(payload))
}

export async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(hashBuffer))
    .map(byte => byte.toString(16).padStart(2, '0'))
    .join('')
}

export function isEncryptedData(value: unknown): value is EncryptedData {
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

interface AccountExportManifest {
  format: 'yumi-account-backup'
  schemaVersion: '1.0.0'
  checksumAlgorithm: 'sha256'
}

interface AccountExportDataBase {
  version: string
  exportedAt: string
  manifest: AccountExportManifest
}

export function isAccountExportData(value: unknown): value is AccountExportDataBase {
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

interface AccountConversation {
  messages?: Array<{ id?: string }>
}

export function countMessages(conversations: Record<string, AccountConversation>): number {
  return Object.values(conversations).reduce((total, conversation) => {
    return total + (conversation.messages?.length ?? 0)
  }, 0)
}

export async function decryptModelSecrets(
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

export function remapImportIds(
  characters: Record<string, AccountCharacter>,
  conversations: Record<
    string,
    { id?: string; accountId?: string; characterId?: string; messages?: Array<{ id?: string }> }
  >,
  config: { activeCharacterId?: string | null },
  accountId: string
): {
  mappedCharacters: Record<string, AccountCharacter>
  mappedConversations: Record<
    string,
    { id?: string; accountId?: string; characterId?: string; messages?: Array<{ id?: string }> }
  >
  finalConfig: { activeCharacterId?: string | null }
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
    const conv = convValue as {
      id?: string
      accountId?: string
      characterId?: string
      messages?: Array<{ id?: string }>
    }
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
