import { describe, it, expect } from 'vitest'
import type { ChatMessage } from '@/types'
import { dedupeMessagesById, mergeMessageHistory, sortMessages } from '@/utils/message'

describe('message utils', () => {
  it('sortMessages orders by timestamp then role tie-break', () => {
    const a: ChatMessage = {
      id: 'b',
      role: 'assistant',
      content: 'a',
      timestamp: '2024-01-01T00:00:00.000Z',
    }
    const u: ChatMessage = {
      id: 'a',
      role: 'user',
      content: 'u',
      timestamp: '2024-01-01T00:00:00.000Z',
    }
    const sorted = sortMessages([a, u])
    expect(sorted[0].role).toBe('user')
    expect(sorted[1].role).toBe('assistant')
  })

  it('dedupeMessagesById keeps last occurrence', () => {
    const m1: ChatMessage = {
      id: '1',
      role: 'user',
      content: 'old',
      timestamp: '2024-01-01T00:00:00.000Z',
    }
    const m2: ChatMessage = {
      id: '1',
      role: 'user',
      content: 'new',
      timestamp: '2024-01-01T00:00:00.000Z',
    }
    const d = dedupeMessagesById([m1, m2])
    expect(d.length).toBe(1)
    expect(d[0].content).toBe('new')
  })

  it('mergeMessageHistory dedupes and sorts', () => {
    const older: ChatMessage = {
      id: 'o1',
      role: 'user',
      content: 'a',
      timestamp: '2024-01-01T00:00:00.000Z',
    }
    const newer: ChatMessage = {
      id: 'n1',
      role: 'assistant',
      content: 'b',
      timestamp: '2024-01-01T00:00:01.000Z',
    }
    const dup: ChatMessage = {
      id: 'o1',
      role: 'user',
      content: 'a2',
      timestamp: '2024-01-01T00:00:00.000Z',
    }
    const merged = mergeMessageHistory([older], [newer, dup])
    expect(merged.length).toBe(2)
    expect(merged[0].id).toBe('o1')
    expect(merged[0].content).toBe('a2')
    expect(merged[1].id).toBe('n1')
  })
})
