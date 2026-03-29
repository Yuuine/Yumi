import { describe, it, expect, vi, beforeEach } from 'vitest'
import { logger, useLogger } from '@/utils/logger'

describe('logger - 日志系统', () => {
  beforeEach(() => {
    const { setConfig } = useLogger()
    setConfig({
      level: 'DEBUG',
      enableConsole: true,
      enableFile: false,
      maxEntries: 100,
    })
    vi.clearAllMocks()
  })

  it('debug 日志正常记录', () => {
    logger.debug('TestModule', 'Debug message')
    const { entries } = useLogger()
    expect(entries.value.some(e => e.message === 'Debug message')).toBe(true)
  })

  it('info 日志正常记录', () => {
    logger.info('TestModule', 'Info message')
    const { entries } = useLogger()
    expect(entries.value.some(e => e.message === 'Info message')).toBe(true)
  })

  it('warn 日志正常记录', () => {
    logger.warn('TestModule', 'Warn message')
    const { entries } = useLogger()
    expect(entries.value.some(e => e.message === 'Warn message')).toBe(true)
  })

  it('error 日志正常记录', () => {
    logger.error('TestModule', 'Error message')
    const { entries } = useLogger()
    expect(entries.value.some(e => e.message === 'Error message')).toBe(true)
  })

  it('日志包含模块名称', () => {
    logger.info('MyModule', 'Test message')
    const { entries } = useLogger()
    const entry = entries.value.find(e => e.message === 'Test message')
    expect(entry?.module).toBe('MyModule')
  })

  it('日志包含时间戳', () => {
    logger.info('TestModule', 'Test message')
    const { entries } = useLogger()
    const entry = entries.value.find(e => e.message === 'Test message')
    expect(entry?.timestamp).toBeTruthy()
    expect(typeof entry?.timestamp).toBe('string')
  })

  it('过滤敏感信息 - API Key', () => {
    const sensitiveMessage = 'apiKey=secret123'
    logger.info('TestModule', sensitiveMessage)
    
    const { entries } = useLogger()
    const entry = entries.value.find(e => e.message.includes('apiKey'))
    expect(entry?.message).not.toContain('secret123')
    expect(entry?.message).toContain('***REDACTED***')
  })

  it('过滤敏感信息 - Bearer Token', () => {
    const sensitiveMessage = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
    logger.info('TestModule', sensitiveMessage)
    
    const { entries } = useLogger()
    const entry = entries.value.find(e => e.message.includes('Authorization'))
    expect(entry?.message).not.toContain('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9')
    expect(entry?.message).toContain('***REDACTED***')
  })

  it('过滤数组中的敏感信息', () => {
    const sensitiveArray = [
      { apiKey: 'secret1' },
      { apiKey: 'secret2' },
      { normal: 'value' },
    ]
    
    logger.info('TestModule', 'Test with array', sensitiveArray)
    
    const { entries } = useLogger()
    const entry = entries.value.find(e => e.message === 'Test with array')
    const data = entry?.data as Array<Record<string, unknown>>
    
    expect(data[0].apiKey).toBe('***REDACTED***')
    expect(data[1].apiKey).toBe('***REDACTED***')
    expect(data[2].normal).toBe('value')
  })
})
