import { describe, it, expect, beforeEach } from 'vitest'
import { saveToStorage, loadFromStorage, clearMessageCache, KEYS } from '@/utils/local-storage'

describe('localStorage 工具函数', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('saveToStorage', () => {
    it('保存数据到 localStorage', () => {
      const data = { name: '测试', value: 123 }
      saveToStorage('test-key', data)
      expect(localStorage.getItem('test-key')).toBe(JSON.stringify(data))
    })

    it('保存 null 到 localStorage', () => {
      saveToStorage('test-null', null)
      expect(localStorage.getItem('test-null')).toBe('null')
    })
  })

  describe('loadFromStorage', () => {
    it('从 localStorage 加载数据', () => {
      const data = { name: '测试', value: 123 }
      localStorage.setItem('test-key', JSON.stringify(data))
      expect(loadFromStorage('test-key', null)).toEqual(data)
    })

    it('键不存在时返回默认值', () => {
      expect(loadFromStorage('non-existent-key', 'default')).toBe('default')
    })

    it('数据无效时返回默认值', () => {
      localStorage.setItem('invalid-json', '{invalid}')
      expect(loadFromStorage('invalid-json', 'default')).toBe('default')
    })
  })

  describe('clearMessageCache', () => {
    it('清除消息缓存', () => {
      localStorage.setItem(KEYS.CACHED_MESSAGES, '[]')
      localStorage.setItem(KEYS.LAST_SYNC, '2024-01-01')
      localStorage.setItem('other-key', 'value')
      
      clearMessageCache()
      
      expect(localStorage.getItem(KEYS.CACHED_MESSAGES)).toBeNull()
      expect(localStorage.getItem(KEYS.LAST_SYNC)).toBeNull()
      expect(localStorage.getItem('other-key')).toBe('value')
    })
  })
})
