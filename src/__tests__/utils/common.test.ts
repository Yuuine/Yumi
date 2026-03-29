import { describe, it, expect } from 'vitest'
import {
  formatDateTime,
  camelToSnake,
  snakeToCamel,
  keysToSnake,
  keysToCamel,
} from '@/utils/common'

describe('common.ts - 通用工具函数', () => {
  describe('formatDateTime', () => {
    it('格式化完整日期时间', () => {
      const date = new Date('2024-01-15T10:30:45Z')
      const result = formatDateTime(date, 'full')
      expect(result).toBeTruthy()
    })

    it('格式化日期部分', () => {
      const date = new Date('2024-01-15T10:30:45Z')
      const result = formatDateTime(date, 'date')
      expect(result).toBeTruthy()
    })

    it('格式化时间部分', () => {
      const date = new Date('2024-01-15T10:30:45Z')
      const result = formatDateTime(date, 'time')
      expect(result).toBeTruthy()
    })

    it('格式化相对时间', () => {
      const date = new Date()
      date.setHours(date.getHours() - 1)
      const result = formatDateTime(date, 'relative')
      expect(result).toBeTruthy()
    })

    it('接受字符串日期输入', () => {
      const result = formatDateTime('2024-01-15T10:30:45Z', 'full')
      expect(result).toBeTruthy()
    })
  })

  describe('camelToSnake', () => {
    it('转换驼峰到蛇形', () => {
      expect(camelToSnake('camelCase')).toBe('camel_case')
      expect(camelToSnake('userId')).toBe('user_id')
      expect(camelToSnake('characterId')).toBe('character_id')
      expect(camelToSnake('APIKey')).toBe('_a_p_i_key')
    })

    it('处理已经是蛇形的字符串', () => {
      expect(camelToSnake('snake_case')).toBe('snake_case')
    })
  })

  describe('snakeToCamel', () => {
    it('转换蛇形到驼峰', () => {
      expect(snakeToCamel('snake_case')).toBe('snakeCase')
      expect(snakeToCamel('user_id')).toBe('userId')
      expect(snakeToCamel('character_id')).toBe('characterId')
    })

    it('处理已经是驼峰的字符串', () => {
      expect(snakeToCamel('camelCase')).toBe('camelCase')
    })
  })

  describe('keysToSnake', () => {
    it('转换对象键名到蛇形', () => {
      const obj = {
        userId: 123,
        userName: 'test',
        characterId: 'char-123',
      }
      const result = keysToSnake(obj)
      expect(result.user_id).toBe(123)
      expect(result.user_name).toBe('test')
      expect(result.character_id).toBe('char-123')
    })

    it('处理嵌套对象', () => {
      const obj = {
        userInfo: {
          userId: 123,
          userName: 'test',
        },
      }
      const result = keysToSnake(obj)
      expect(result.user_info).toBeTruthy()
      const nested = result.user_info as Record<string, unknown>
      expect(nested.user_id).toBe(123)
    })

    it('处理数组', () => {
      const obj = {
        items: [
          { itemId: 1, itemName: 'a' },
          { itemId: 2, itemName: 'b' },
        ],
      }
      const result = keysToSnake(obj)
      const items = result.items as Array<Record<string, unknown>>
      expect(items[0].item_id).toBe(1)
      expect(items[1].item_id).toBe(2)
    })

    it('处理 null 和 undefined', () => {
      expect(keysToSnake(null as any)).toBeNull()
    })
  })

  describe('keysToCamel', () => {
    it('转换对象键名到驼峰', () => {
      const obj = {
        user_id: 123,
        user_name: 'test',
        character_id: 'char-123',
      }
      const result = keysToCamel(obj)
      expect(result.userId).toBe(123)
      expect(result.userName).toBe('test')
      expect(result.characterId).toBe('char-123')
    })

    it('处理嵌套对象', () => {
      const obj = {
        user_info: {
          user_id: 123,
          user_name: 'test',
        },
      }
      const result = keysToCamel(obj)
      expect(result.userInfo).toBeTruthy()
      const nested = result.userInfo as Record<string, unknown>
      expect(nested.userId).toBe(123)
    })

    it('处理数组', () => {
      const obj = {
        items: [
          { item_id: 1, item_name: 'a' },
          { item_id: 2, item_name: 'b' },
        ],
      }
      const result = keysToCamel(obj)
      const items = result.items as Array<Record<string, unknown>>
      expect(items[0].itemId).toBe(1)
      expect(items[1].itemId).toBe(2)
    })

    it('处理 null 和 undefined', () => {
      expect(keysToCamel(null as any)).toBeNull()
    })
  })
})
