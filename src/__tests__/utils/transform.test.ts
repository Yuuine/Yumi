import { describe, it, expect } from 'vitest'
import { convertObjectKeys, keysToSnake, keysToCamel } from '@/utils/transform'

describe('transform.ts - 对象键名转换', () => {
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
    })

    it('处理 null 和 undefined', () => {
      expect(keysToCamel(null as any)).toBeNull()
    })
  })

  describe('convertObjectKeys (deprecated)', () => {
    it('camelToSnake 转换', () => {
      const obj = {
        userId: 123,
        userName: 'test',
      }
      const result = convertObjectKeys(obj, 'camelToSnake')
      expect(result.user_id).toBe(123)
      expect(result.user_name).toBe('test')
    })

    it('snakeToCamel 转换', () => {
      const obj = {
        user_id: 123,
        user_name: 'test',
      }
      const result = convertObjectKeys(obj, 'snakeToCamel')
      expect(result.userId).toBe(123)
      expect(result.userName).toBe('test')
    })
  })
})
