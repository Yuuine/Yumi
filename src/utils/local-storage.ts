import { logger } from '@/utils/logger'

/**
 * 本地存储工具
 * 用于持久化用户设置和缓存数据
 */

const KEYS = {
  USER_ID: 'yumi_user_id',
  SETTINGS: 'yumi_settings',
  CACHED_MESSAGES: 'yumi_cached_messages',
  LAST_SYNC: 'yumi_last_sync',
} as const

const MAX_CACHED_MESSAGES = 100

/**
 * 保存数据到 localStorage
 */
export function saveToStorage<T>(key: string, data: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(data))
  } catch (error) {
    logger.error('LocalStorage', 'Failed to save to localStorage', error)
  }
}

/**
 * 从 localStorage 读取数据
 */
export function loadFromStorage<T>(key: string, defaultValue: T): T {
  try {
    const data = localStorage.getItem(key)
    return data ? JSON.parse(data) : defaultValue
  } catch (error) {
    logger.error('LocalStorage', 'Failed to load from localStorage', error)
    return defaultValue
  }
}

/**
 * 从 localStorage 删除数据
 */
export function removeFromStorage(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch (error) {
    logger.error('LocalStorage', 'Failed to remove from localStorage', error)
  }
}

/**
 * 缓存消息到本地
 */
export function cacheMessages(messages: unknown[]): void {
  const limitedMessages = messages.slice(-MAX_CACHED_MESSAGES)
  saveToStorage(KEYS.CACHED_MESSAGES, limitedMessages)
  saveToStorage(KEYS.LAST_SYNC, new Date().toISOString())
}

/**
 * 获取缓存的消息
 */
export function getCachedMessages<T>(): T[] {
  return loadFromStorage<T[]>(KEYS.CACHED_MESSAGES, [])
}

/**
 * 清除所有缓存数据
 */
export function clearAllCache(): void {
  Object.values(KEYS).forEach(key => {
    removeFromStorage(key)
  })
}

/**
 * 清除聊天缓存，不影响登录身份
 */
export function clearMessageCache(): void {
  removeFromStorage(KEYS.CACHED_MESSAGES)
  removeFromStorage(KEYS.LAST_SYNC)
}

export { KEYS, MAX_CACHED_MESSAGES }
