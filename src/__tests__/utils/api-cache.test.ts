import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiCache } from '@/utils/api-cache'

vi.mock('@/utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

describe('api-cache - API缓存系统', () => {
  beforeEach(() => {
    apiCache.clear()
  })

  it('set 和 get 正常工作', () => {
    const data = { message: 'test data' }

    apiCache.set('GET', '/api/test', data)
    const result = apiCache.get('GET', '/api/test')

    expect(result).toEqual(data)
  })

  it('get 不存在的键返回 null', () => {
    const result = apiCache.get('GET', '/api/nonexistent')
    expect(result).toBeNull()
  })

  it('过期的缓存返回 null', () => {
    const data = { message: 'test data' }

    vi.useFakeTimers()
    apiCache.set('GET', '/api/test', data, 1000)

    vi.advanceTimersByTime(1500)

    const result = apiCache.get('GET', '/api/test')
    expect(result).toBeNull()

    vi.useRealTimers()
  })

  it('未过期的缓存正常返回', () => {
    const data = { message: 'test data' }

    vi.useFakeTimers()
    apiCache.set('GET', '/api/test', data, 5000)

    vi.advanceTimersByTime(1000)

    const result = apiCache.get('GET', '/api/test')
    expect(result).toEqual(data)

    vi.useRealTimers()
  })

  it('考虑查询参数的缓存键', () => {
    const data1 = { message: 'data 1' }
    const data2 = { message: 'data 2' }

    apiCache.set('GET', '/api/test', data1, 300000, { id: 1 })
    apiCache.set('GET', '/api/test', data2, 300000, { id: 2 })

    const result1 = apiCache.get('GET', '/api/test', { id: 1 })
    const result2 = apiCache.get('GET', '/api/test', { id: 2 })

    expect(result1).toEqual(data1)
    expect(result2).toEqual(data2)
  })

  it('查询参数的顺序不影响缓存键', () => {
    const data = { message: 'test data' }

    apiCache.set('GET', '/api/test', data, 300000, { a: 1, b: 2 })

    const result = apiCache.get('GET', '/api/test', { b: 2, a: 1 })

    expect(result).toEqual(data)
  })

  it('invalidate 使特定的缓存失效', () => {
    const data = { message: 'test data' }

    apiCache.set('GET', '/api/test', data)
    apiCache.invalidate('GET', '/api/test')

    const result = apiCache.get('GET', '/api/test')
    expect(result).toBeNull()
  })

  it('invalidatePattern 使匹配模式的缓存失效', () => {
    const data1 = { message: 'data 1' }
    const data2 = { message: 'data 2' }

    apiCache.set('GET', '/api/user/1', data1)
    apiCache.set('GET', '/api/user/2', data2)
    apiCache.set('GET', '/api/posts', {})

    apiCache.invalidatePattern('/api/user')

    const result1 = apiCache.get('GET', '/api/user/1')
    const result2 = apiCache.get('GET', '/api/user/2')
    const result3 = apiCache.get('GET', '/api/posts')

    expect(result1).toBeNull()
    expect(result2).toBeNull()
    expect(result3).not.toBeNull()
  })

  it('clear 清除所有缓存', () => {
    const data1 = { message: 'data 1' }
    const data2 = { message: 'data 2' }

    apiCache.set('GET', '/api/test1', data1)
    apiCache.set('GET', '/api/test2', data2)

    apiCache.clear()

    const result1 = apiCache.get('GET', '/api/test1')
    const result2 = apiCache.get('GET', '/api/test2')

    expect(result1).toBeNull()
    expect(result2).toBeNull()
  })

  it('getStats 返回正确的统计信息', () => {
    apiCache.set('GET', '/api/test', { data: 'test' })

    apiCache.get('GET', '/api/test')
    apiCache.get('GET', '/api/test')
    apiCache.get('GET', '/api/nonexistent')

    const stats = apiCache.getStats()

    expect(stats.hits).toBe(2)
    expect(stats.misses).toBe(1)
    expect(stats.size).toBe(1)
  })

  it('getHitRate 返回正确的命中率', () => {
    apiCache.set('GET', '/api/test', { data: 'test' })

    apiCache.get('GET', '/api/test')
    apiCache.get('GET', '/api/test')
    apiCache.get('GET', '/api/nonexistent')

    const hitRate = apiCache.getHitRate()

    expect(hitRate).toBe(2 / 3)
  })

  it('getHitRate 没有请求时返回 0', () => {
    const hitRate = apiCache.getHitRate()
    expect(hitRate).toBe(0)
  })

  it('不同的 HTTP 方法使用不同的缓存', () => {
    const data1 = { message: 'GET data' }
    const data2 = { message: 'POST data' }

    apiCache.set('GET', '/api/test', data1)
    apiCache.set('POST', '/api/test', data2)

    const result1 = apiCache.get('GET', '/api/test')
    const result2 = apiCache.get('POST', '/api/test')

    expect(result1).toEqual(data1)
    expect(result2).toEqual(data2)
  })

  it('clear 重置统计信息', () => {
    apiCache.set('GET', '/api/test', { data: 'test' })
    apiCache.get('GET', '/api/test')
    apiCache.get('GET', '/api/nonexistent')

    apiCache.clear()

    const stats = apiCache.getStats()

    expect(stats.hits).toBe(0)
    expect(stats.misses).toBe(0)
    expect(stats.size).toBe(0)
  })
})
