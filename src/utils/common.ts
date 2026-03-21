/**
 * 通用工具函数
 */

import { formatRelativeTime, formatDateTime as formatDateTimeBase } from './datetime'

/**
 * 格式化日期时间
 * @param date - 日期对象或字符串
 * @param format - 格式类型
 * @returns 格式化后的日期字符串
 */
export function formatDateTime(
  date: Date | string,
  format: 'full' | 'date' | 'time' | 'relative' = 'full'
): string {
  const d = typeof date === 'string' ? new Date(date) : date

  if (format === 'relative') {
    return formatRelativeTime(d)
  }

  const formatMap: Record<string, string> = {
    date: 'YYYY-MM-DD',
    time: 'HH:mm',
    full: 'YYYY-MM-DD HH:mm:ss',
  }

  return formatDateTimeBase(d, formatMap[format])
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    const success = document.execCommand('copy')
    document.body.removeChild(textarea)
    return success
  }
}

export function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
}

export function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

export function keysToSnake<T extends Record<string, unknown>>(obj: T): Record<string, unknown> {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map(item => keysToSnake(item as Record<string, unknown>)) as unknown as Record<
      string,
      unknown
    >
  }

  const result: Record<string, unknown> = {}
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const snakeKey = camelToSnake(key)
      const value = obj[key]
      result[snakeKey] =
        value !== null && typeof value === 'object'
          ? keysToSnake(value as Record<string, unknown>)
          : value
    }
  }
  return result
}

export function keysToCamel<T extends Record<string, unknown>>(obj: T): Record<string, unknown> {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map(item => keysToCamel(item as Record<string, unknown>)) as unknown as Record<
      string,
      unknown
    >
  }

  const result: Record<string, unknown> = {}
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const camelKey = snakeToCamel(key)
      const value = obj[key]
      result[camelKey] =
        value !== null && typeof value === 'object'
          ? keysToCamel(value as Record<string, unknown>)
          : value
    }
  }
  return result
}
