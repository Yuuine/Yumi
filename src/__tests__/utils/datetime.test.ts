import { describe, it, expect } from 'vitest'
import { formatRelativeTime, formatDateTime } from '@/utils/datetime'

describe('datetime 工具函数', () => {
  describe('formatRelativeTime', () => {
    it('格式化相对时间', () => {
      const now = new Date()
      
      const result = formatRelativeTime(now.toISOString())
      expect(typeof result).toBe('string')
      
      const oneMinuteAgo = new Date(now.getTime() - 60 * 1000)
      const result2 = formatRelativeTime(oneMinuteAgo.toISOString())
      expect(typeof result2).toBe('string')
    })
  })

  describe('formatDateTime', () => {
    it('格式化日期时间', () => {
      const date = new Date('2024-01-15T10:30:00')
      expect(formatDateTime(date.toISOString(), 'YYYY-MM-DD HH:mm')).toBe('2024-01-15 10:30')
    })
  })
})
