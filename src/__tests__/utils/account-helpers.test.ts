import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  generateAccountId,
  generateCharacterId,
  generateConversationId,
  generateMessageId,
  generateSecretId,
  buildChecksumSource,
  isEncryptedData,
  isAccountExportData,
  countMessages,
  sha256Hex,
  decryptModelSecrets,
  remapImportIds,
} from '@/utils/account-helpers'
import * as cryptoService from '@/utils/crypto-service'

vi.mock('@/utils/crypto-service', () => ({
  decrypt: vi.fn(),
}))

describe('account-helpers.ts - 账户辅助工具', () => {
  describe('ID 生成函数', () => {
    it('generateAccountId 生成账户ID', () => {
      const id = generateAccountId()
      expect(id).toBeTruthy()
      expect(id.startsWith('acc_')).toBe(true)
    })

    it('generateCharacterId 生成角色ID', () => {
      const id = generateCharacterId()
      expect(id).toBeTruthy()
      expect(id.startsWith('char_')).toBe(true)
    })

    it('generateConversationId 生成对话ID', () => {
      const id = generateConversationId()
      expect(id).toBeTruthy()
      expect(id.startsWith('conv_')).toBe(true)
    })

    it('generateMessageId 生成消息ID', () => {
      const id = generateMessageId()
      expect(id).toBeTruthy()
      expect(id.startsWith('msg_')).toBe(true)
    })

    it('generateSecretId 生成密钥ID', () => {
      const id = generateSecretId()
      expect(id).toBeTruthy()
      expect(id.startsWith('secret_')).toBe(true)
    })

    it('生成的ID都是唯一的', () => {
      const ids = new Set()
      for (let i = 0; i < 100; i++) {
        const id = generateAccountId()
        expect(ids.has(id)).toBe(false)
        ids.add(id)
      }
    })
  })

  describe('buildChecksumSource', () => {
    it('构建校验和源', () => {
      const payload = {
        b: 2,
        a: 1,
        c: { z: 3, y: 4 },
      }
      const result = buildChecksumSource(payload)
      expect(result).toBeTruthy()
      expect(typeof result).toBe('string')
    })

    it('对相同的对象生成相同的字符串', () => {
      const payload1 = { a: 1, b: 2 }
      const payload2 = { b: 2, a: 1 }
      const result1 = buildChecksumSource(payload1)
      const result2 = buildChecksumSource(payload2)
      expect(result1).toEqual(result2)
    })

    it('数组会被递归处理但不改变元素顺序', () => {
      const payload1 = [3, 1, 2]
      const payload2 = [3, 1, 2]
      const result1 = buildChecksumSource(payload1)
      const result2 = buildChecksumSource(payload2)
      expect(result1).toEqual(result2)
    })

    it('对原始值直接返回', () => {
      expect(buildChecksumSource('test')).toEqual('"test"')
      expect(buildChecksumSource(123)).toEqual('123')
      expect(buildChecksumSource(null)).toEqual('null')
      expect(buildChecksumSource(undefined)).toEqual(undefined)
    })
  })

  describe('isEncryptedData', () => {
    it('识别有效的加密数据', () => {
      const data = {
        ciphertext: 'encrypted',
        iv: 'iv',
        salt: 'salt',
      }
      expect(isEncryptedData(data)).toBe(true)
    })

    it('识别无效的加密数据', () => {
      expect(isEncryptedData(null)).toBe(false)
      expect(isEncryptedData(undefined)).toBe(false)
      expect(isEncryptedData('string')).toBe(false)
      expect(isEncryptedData(123)).toBe(false)
      expect(isEncryptedData({})).toBe(false)
      expect(isEncryptedData({ ciphertext: 'only' })).toBe(false)
    })
  })

  describe('isAccountExportData', () => {
    it('识别有效的账户导出数据', () => {
      const data = {
        version: '1.0.0',
        exportedAt: new Date().toISOString(),
        manifest: {
          format: 'yumi-account-backup',
          schemaVersion: '1.0.0',
          checksumAlgorithm: 'sha256',
        },
      }
      expect(isAccountExportData(data)).toBe(true)
    })

    it('识别无效的账户导出数据', () => {
      expect(isAccountExportData(null)).toBe(false)
      expect(isAccountExportData(undefined)).toBe(false)
      expect(isAccountExportData({})).toBe(false)
      expect(isAccountExportData({ version: '1.0.0' })).toBe(false)
    })
  })

  describe('countMessages', () => {
    it('统计对话中的消息数量', () => {
      const conversations = {
        conv1: { messages: [{ id: '1' }, { id: '2' }] },
        conv2: { messages: [{ id: '3' }] },
        conv3: {},
      }
      const count = countMessages(conversations)
      expect(count).toBe(3)
    })

    it('没有消息时返回0', () => {
      const count = countMessages({})
      expect(count).toBe(0)
    })

    it('messages 为 undefined 时正确处理', () => {
      const conversations = {
        conv1: {},
        conv2: { messages: undefined },
      }
      const count = countMessages(conversations)
      expect(count).toBe(0)
    })
  })

  describe('sha256Hex', () => {
    it('计算 SHA-256 哈希', async () => {
      const hash = await sha256Hex('test')
      expect(hash).toBeTruthy()
      expect(typeof hash).toBe('string')
      expect(hash.length).toBe(64)
    })

    it('相同输入生成相同哈希', async () => {
      const hash1 = await sha256Hex('same input')
      const hash2 = await sha256Hex('same input')
      expect(hash1).toEqual(hash2)
    })

    it('不同输入生成不同哈希', async () => {
      const hash1 = await sha256Hex('input 1')
      const hash2 = await sha256Hex('input 2')
      expect(hash1).not.toEqual(hash2)
    })

    it('空字符串也能生成哈希', async () => {
      const hash = await sha256Hex('')
      expect(hash).toBeTruthy()
      expect(hash.length).toBe(64)
    })
  })

  describe('decryptModelSecrets', () => {
    beforeEach(() => {
      vi.clearAllMocks()
    })

    it('解密有 apiSecret 的模型', async () => {
      const mockDecrypt = vi.mocked(cryptoService.decrypt)
      mockDecrypt.mockResolvedValueOnce(JSON.stringify({ apiKey: 'decrypted-key', apiSecret: 'decrypted-secret' }))

      const models = [
        {
          id: '1',
          apiKey: 'encrypted-key',
          apiSecret: JSON.stringify({ iv: 'iv', salt: 'salt' }),
        },
      ]

      const result = await decryptModelSecrets(models, 'password')
      expect(result.length).toBe(1)
      expect(result[0].apiKey).toBe('decrypted-key')
      expect(result[0].apiSecret).toBe('decrypted-secret')
      expect(mockDecrypt).toHaveBeenCalledTimes(1)
    })

    it('跳过没有 apiSecret 的模型', async () => {
      const models = [
        {
          id: '1',
          apiKey: 'plain-key',
          apiSecret: undefined,
        },
      ]

      const result = await decryptModelSecrets(models, 'password')
      expect(result.length).toBe(1)
      expect(result[0].apiKey).toBe('plain-key')
      expect(result[0].apiSecret).toBeUndefined()
    })

    it('解密失败时跳过该模型', async () => {
      const mockDecrypt = vi.mocked(cryptoService.decrypt)
      mockDecrypt.mockRejectedValueOnce(new Error('Decryption failed'))

      const models = [
        {
          id: '1',
          apiKey: 'encrypted-key',
          apiSecret: JSON.stringify({ iv: 'iv', salt: 'salt' }),
        },
      ]

      const result = await decryptModelSecrets(models, 'password')
      expect(result.length).toBe(0)
    })

    it('处理空模型列表', async () => {
      const result = await decryptModelSecrets([], 'password')
      expect(result.length).toBe(0)
    })

    it('混合模型 - 部分解密成功，部分失败', async () => {
      const mockDecrypt = vi.mocked(cryptoService.decrypt)
      mockDecrypt
        .mockResolvedValueOnce(JSON.stringify({ apiKey: 'success-key', apiSecret: 'success-secret' }))
        .mockRejectedValueOnce(new Error('Failed'))

      const models = [
        {
          id: '1',
          apiKey: 'key1',
          apiSecret: JSON.stringify({ iv: 'iv1', salt: 'salt1' }),
        },
        {
          id: '2',
          apiKey: 'key2',
          apiSecret: JSON.stringify({ iv: 'iv2', salt: 'salt2' }),
        },
        {
          id: '3',
          apiKey: 'plain-key',
          apiSecret: undefined,
        },
      ]

      const result = await decryptModelSecrets(models, 'password')
      expect(result.length).toBe(2)
      expect(result[0].id).toBe('1')
      expect(result[1].id).toBe('3')
    })
  })

  describe('remapImportIds', () => {
    it('重新映射角色和对话ID', () => {
      const characters = {
        char1: { id: 'char1', name: 'Character 1', accountId: 'old-acc' } as any,
      }
      const conversations = {
        conv1: { id: 'conv1', accountId: 'old-acc', characterId: 'char1', messages: [{ id: 'msg1' }] },
      }
      const config = { activeCharacterId: 'char1' }
      const accountId = 'new-acc-id'

      const result = remapImportIds(characters, conversations, config, accountId)

      expect(result.mappedCharacters).toBeTruthy()
      expect(result.mappedConversations).toBeTruthy()
      expect(result.finalConfig).toBeTruthy()

      const charValues = Object.values(result.mappedCharacters)
      expect(charValues[0].accountId).toBe(accountId)
      expect(charValues[0].id).not.toBe('char1')
      expect(charValues[0].id).toMatch(/^char_/)

      const convValues = Object.values(result.mappedConversations)
      expect(convValues[0].accountId).toBe(accountId)
      expect(convValues[0].id).not.toBe('conv1')
      expect(convValues[0].id).toMatch(/^conv_/)
      expect(convValues[0].characterId).toBe(charValues[0].id)
    })

    it('没有 activeCharacterId 时使用第一个角色', () => {
      const characters = {
        char1: { id: 'char1', name: 'Character 1' } as any,
        char2: { id: 'char2', name: 'Character 2' } as any,
      }
      const conversations = {}
      const config = { activeCharacterId: null }
      const accountId = 'new-acc-id'

      const result = remapImportIds(characters, conversations, config, accountId)
      const charValues = Object.values(result.mappedCharacters)
      expect(result.finalConfig.activeCharacterId).toBe(charValues[0].id)
    })

    it('活跃角色不存在时使用第一个角色', () => {
      const characters = {
        char1: { id: 'char1', name: 'Character 1' } as any,
      }
      const conversations = {}
      const config = { activeCharacterId: 'non-existent-id' }
      const accountId = 'new-acc-id'

      const result = remapImportIds(characters, conversations, config, accountId)
      const charValues = Object.values(result.mappedCharacters)
      expect(result.finalConfig.activeCharacterId).toBe(charValues[0].id)
    })

    it('没有角色时保持配置不变', () => {
      const characters = {}
      const conversations = {}
      const config = { activeCharacterId: null }
      const accountId = 'new-acc-id'

      const result = remapImportIds(characters, conversations, config, accountId)
      expect(result.finalConfig).toEqual(config)
    })

    it('消息没有id时生成新id', () => {
      const characters = {}
      const conversations = {
        conv1: { messages: [{ id: 'existing' }, {}] },
      }
      const config = {}
      const accountId = 'new-acc-id'

      const result = remapImportIds(characters, conversations, config, accountId)
      const convValues = Object.values(result.mappedConversations)
      expect(convValues[0].messages![0].id).toBe('existing')
      expect(convValues[0].messages![1].id).toBeTruthy()
      expect(convValues[0].messages![1].id).toMatch(/^msg_/)
    })
  })
})
