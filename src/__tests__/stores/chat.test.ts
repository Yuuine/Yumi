import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'

vi.mock('@/api/chat', () => ({
  chatApi: {
    sendMessage: vi.fn(),
    getHistory: vi.fn(),
  },
}))

vi.mock('@/api/http-client', () => ({
  httpClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
  ApiError: class ApiError {
    constructor(
      public code: string,
      public message: string
    ) {}
  },
}))

describe('useChatStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should initialize with empty messages', () => {
    const store = useChatStore()

    expect(store.messages).toEqual([])
    expect(store.isLoading).toBe(false)
    expect(store.conversationCount).toBe(0)
  })

  it('should clear messages', () => {
    const store = useChatStore()

    store.messages.push({ id: '1', role: 'user', content: 'test', timestamp: '2024-01-01' })
    store.conversationCount = 5

    store.clearMessages()

    expect(store.messages).toEqual([])
    expect(store.conversationCount).toBe(0)
  })

  it('should clear error', () => {
    const store = useChatStore()

    store.lastError = { code: 'TEST', message: 'Test error' }
    store.clearError()

    expect(store.lastError).toBeNull()
  })

  it('should compute recentMessages correctly', () => {
    const store = useChatStore()

    for (let i = 0; i < 25; i++) {
      store.messages.push({
        id: `${i}`,
        role: 'user',
        content: `Message ${i}`,
        timestamp: `2024-01-01T00:00:${i.toString().padStart(2, '0')}Z`,
      })
    }

    expect(store.recentMessages.length).toBe(20)
    expect(store.recentMessages[0].id).toBe('5')
  })

  it('should compute userMessages correctly', () => {
    const store = useChatStore()

    store.messages.push(
      { id: '1', role: 'user', content: 'User message', timestamp: '' },
      { id: '2', role: 'assistant', content: 'Assistant message', timestamp: '' },
      { id: '3', role: 'user', content: 'Another user message', timestamp: '' }
    )

    expect(store.userMessages.length).toBe(2)
  })

  it('should not send empty message', async () => {
    const store = useChatStore()

    const result = await store.sendMessage('')

    expect(result).toBeNull()
    expect(store.messages.length).toBe(0)
  })

  it('should not send message when loading', async () => {
    const store = useChatStore()

    store.isLoading = true

    const result = await store.sendMessage('test message')

    expect(result).toBeNull()
  })
})
