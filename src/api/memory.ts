import type { MemorySearchResult, MemoryStats } from '@/types'
import { httpClient } from './http-client'

export interface MemorySearchRequest {
  query: string
  topK?: number
  decayDays?: boolean
}

export const memoryApi = {
  async search(request: MemorySearchRequest): Promise<MemorySearchResult> {
    return httpClient.get<MemorySearchResult>('/memory/search', {
      params: {
        query: request.query,
        top_k: request.topK || 6,
        decay_days: request.decayDays ?? true,
      },
    })
  },

  async getStats(userId: string): Promise<MemoryStats> {
    return httpClient.get<MemoryStats>('/memory/stats', {
      params: { userId },
    })
  },
}
