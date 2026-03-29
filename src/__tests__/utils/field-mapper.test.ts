import { describe, it, expect } from 'vitest'
import {
  toCamelCase,
  toSnakeCase,
  toCamelCaseStr,
  toSnakeCaseStr,
  toConversationDTO,
  toConversationListDTO,
  conversationToBackend,
  toCharacterCardDTO,
  toCharacterCardListDTO,
  characterCardToBackend,
} from '@/utils/field-mapper'

describe('field-mapper.ts - 字段映射工具', () => {
  describe('字符串转换', () => {
    it('toSnakeCaseStr 转换驼峰到蛇形', () => {
      expect(toSnakeCaseStr('camelCase')).toBe('camel_case')
      expect(toSnakeCaseStr('userId')).toBe('user_id')
      expect(toSnakeCaseStr('characterId')).toBe('character_id')
    })

    it('toCamelCaseStr 转换蛇形到驼峰', () => {
      expect(toCamelCaseStr('snake_case')).toBe('snakeCase')
      expect(toCamelCaseStr('user_id')).toBe('userId')
      expect(toCamelCaseStr('character_id')).toBe('characterId')
    })
  })

  describe('对象键名转换', () => {
    it('toSnakeCase 转换对象到蛇形', () => {
      const obj = {
        userId: 123,
        userName: 'test',
        characterId: 'char-123',
      }
      const result = toSnakeCase(obj) as any
      expect(result.user_id).toBe(123)
      expect(result.user_name).toBe('test')
      expect(result.character_id).toBe('char-123')
    })

    it('toCamelCase 转换对象到驼峰', () => {
      const obj = {
        user_id: 123,
        user_name: 'test',
        character_id: 'char-123',
      }
      const result = toCamelCase(obj) as any
      expect(result.userId).toBe(123)
      expect(result.userName).toBe('test')
      expect(result.characterId).toBe('char-123')
    })

    it('toSnakeCase 处理嵌套对象', () => {
      const obj = {
        userInfo: {
          userId: 123,
          userName: 'test',
        },
      }
      const result = toSnakeCase(obj) as any
      expect(result.user_info).toBeTruthy()
    })

    it('toCamelCase 处理嵌套对象', () => {
      const obj = {
        user_info: {
          user_id: 123,
          user_name: 'test',
        },
      }
      const result = toCamelCase(obj) as any
      expect(result.userInfo).toBeTruthy()
    })

    it('toSnakeCase 处理数组', () => {
      const obj = {
        items: [
          { itemId: 1, itemName: 'a' },
          { itemId: 2, itemName: 'b' },
        ],
      }
      const result = toSnakeCase(obj)
      const items = result.items as Array<Record<string, unknown>>
      expect(items[0].item_id).toBe(1)
    })

    it('toCamelCase 处理数组', () => {
      const obj = {
        items: [
          { item_id: 1, item_name: 'a' },
          { item_id: 2, item_name: 'b' },
        ],
      }
      const result = toCamelCase(obj)
      const items = result.items as Array<Record<string, unknown>>
      expect(items[0].itemId).toBe(1)
    })

    it('toSnakeCase 处理 null 和 undefined', () => {
      expect(toSnakeCase(null as any)).toBeNull()
      expect(toSnakeCase(undefined as any)).toBeUndefined()
    })

    it('toCamelCase 处理 null 和 undefined', () => {
      expect(toCamelCase(null as any)).toBeNull()
      expect(toCamelCase(undefined as any)).toBeUndefined()
    })
  })

  describe('对话 DTO 转换', () => {
    it('toConversationDTO 转换对话数据', () => {
      const raw = {
        id: 'conv-123',
        user_id: 'user-123',
        character_id: 'char-123',
        title: '测试对话',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-02',
      }
      const result = toConversationDTO(raw)
      expect(result.id).toBe('conv-123')
      expect(result.userId).toBe('user-123')
      expect(result.characterId).toBe('char-123')
      expect(result.title).toBe('测试对话')
      expect(result.isActive).toBe(true)
      expect(result.createdAt).toBe('2024-01-01')
      expect(result.updatedAt).toBe('2024-01-02')
    })

    it('toConversationListDTO 转换对话列表', () => {
      const rawList = [{ id: 'conv-1' }, { id: 'conv-2' }]
      const result = toConversationListDTO(rawList)
      expect(result.length).toBe(2)
    })

    it('conversationToBackend 转换对话到后端格式', () => {
      const data = {
        id: 'conv-123',
        userId: 'user-123',
        characterId: 'char-123',
        title: '测试对话',
        isActive: true,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-02',
      }
      const result = conversationToBackend(data)
      expect(result.id).toBe('conv-123')
      expect(result.user_id).toBe('user-123')
      expect(result.character_id).toBe('char-123')
      expect(result.title).toBe('测试对话')
      expect(result.is_active).toBe(true)
      expect(result.created_at).toBe('2024-01-01')
      expect(result.updated_at).toBe('2024-01-02')
    })
  })

  describe('角色卡 DTO 转换', () => {
    it('toCharacterCardDTO 转换角色卡数据', () => {
      const raw = {
        id: 'char-123',
        user_id: 'user-123',
        conversation_id: 'conv-123',
        role_overview: '测试角色',
        formal_name: '艾拉',
        nickname: '艾拉酱',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-02',
      }
      const result = toCharacterCardDTO(raw)
      expect(result.id).toBe('char-123')
      expect(result.userId).toBe('user-123')
      expect(result.conversationId).toBe('conv-123')
      expect(result.roleOverview).toBe('测试角色')
      expect(result.formalName).toBe('艾拉')
      expect(result.nickname).toBe('艾拉酱')
      expect(result.isActive).toBe(true)
      expect(result.createdAt).toBe('2024-01-01')
      expect(result.updatedAt).toBe('2024-01-02')
    })

    it('toCharacterCardListDTO 转换角色卡列表', () => {
      const rawList = [{ id: 'char-1' }, { id: 'char-2' }]
      const result = toCharacterCardListDTO(rawList)
      expect(result.length).toBe(2)
    })

    it('characterCardToBackend 转换角色卡到后端格式', () => {
      const data = {
        id: 'char-123',
        userId: 'user-123',
        conversationId: 'conv-123',
        roleOverview: '测试角色',
        formalName: '艾拉',
        nickname: '艾拉酱',
        isActive: true,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-02',
      }
      const result = characterCardToBackend(data)
      expect(result.id).toBe('char-123')
      expect(result.user_id).toBe('user-123')
      expect(result.conversation_id).toBe('conv-123')
      expect(result.role_overview).toBe('测试角色')
      expect(result.formal_name).toBe('艾拉')
      expect(result.nickname).toBe('艾拉酱')
      expect(result.is_active).toBe(true)
      expect(result.created_at).toBe('2024-01-01')
      expect(result.updated_at).toBe('2024-01-02')
    })
  })
})
