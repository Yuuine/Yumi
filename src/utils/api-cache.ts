import { logger } from '@/utils/logger'

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

interface CacheStats {
  hits: number
  misses: number
  size: number
}

class ApiCache {
  private cache = new Map<string, CacheEntry<unknown>>()
  private hits = 0
  private misses = 0

  private generateKey(method: string, url: string, params?: Record<string, unknown>): string {
    const sortedParams = params
      ? Object.keys(params)
          .sort()
          .reduce(
            (acc, key) => {
              acc[key] = params[key]
              return acc
            },
            {} as Record<string, unknown>
          )
      : {}
    return `${method}:${url}:${JSON.stringify(sortedParams)}`
  }

  get<T>(method: string, url: string, params?: Record<string, unknown>): T | null {
    const key = this.generateKey(method, url, params)
    const entry = this.cache.get(key) as CacheEntry<T> | undefined

    if (!entry) {
      this.misses++
      logger.debug('ApiCache', 'Cache MISS', { key })
      return null
    }

    const now = Date.now()
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      this.misses++
      logger.debug('ApiCache', 'Cache EXPIRED', { key })
      return null
    }

    this.hits++
    logger.debug('ApiCache', 'Cache HIT', { key })
    return entry.data
  }

  set<T>(
    method: string,
    url: string,
    data: T,
    ttl = 300000,
    params?: Record<string, unknown>
  ): void {
    const key = this.generateKey(method, url, params)
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    })
    logger.debug('ApiCache', 'Cache SET', { key, ttl })
  }

  invalidate(method: string, url: string, params?: Record<string, unknown>): void {
    const key = this.generateKey(method, url, params)
    this.cache.delete(key)
    logger.debug('ApiCache', 'Cache INVALIDATED', { key })
  }

  invalidatePattern(pattern: string): void {
    const keysToDelete: string[] = []
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach(key => this.cache.delete(key))
    logger.debug('ApiCache', 'Cache INVALIDATED BY PATTERN', {
      pattern,
      count: keysToDelete.length,
    })
  }

  clear(): void {
    this.cache.clear()
    this.hits = 0
    this.misses = 0
    logger.debug('ApiCache', 'Cache CLEARED')
  }

  getStats(): CacheStats {
    return {
      hits: this.hits,
      misses: this.misses,
      size: this.cache.size,
    }
  }

  getHitRate(): number {
    const total = this.hits + this.misses
    return total === 0 ? 0 : this.hits / total
  }
}

export const apiCache = new ApiCache()
