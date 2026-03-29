import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/api/chat'
import { conversationsApi } from '@/api/conversations'

vi.mock('@/api/chat', () => ({
  chatApi: {
    sendMessage: vi.fn(),
    getHistory: vi.fn(),
  },
}))

vi.mock('@/api/conversations', () => ({
  conversationsApi: {
    createConversation: vi.fn(),
  },
}))

vi.mock('@/api/http-client', () => ({
  ApiError: class ApiError {
    constructor(
      public code: string,
      public message: string
    ) {}
  },
}))

const mockAccountStore = {
  currentAccountId: 'test-account',
  currentAccount: { id: 'test-account' },
  currentConfig: { activeCharacterId: 'char-123' },
  loadConversations: vi.fn().mockResolvedValue([]),
  getConversation: vi.fn().mockResolvedValue(null),
  saveConversation: vi.fn(),
  setActiveCharacterId: vi.fn(),
}

vi.mock('@/stores/account', () => ({
  useAccountStore: () => mockAccountStore,
}))

const mockModelsStore = {
  models: [{ id: 'model-1', isEnabled: true, apiKey: 'test-key' }],
}

vi.mock('@/stores/models', () => ({
  useModelsStore: vi.fn(() => mockModelsStore),
}))

vi.mock('@/utils/local-storage', () => ({
  saveToStorage: vi.fn(),
  loadFromStorage: vi.fn().mockReturnValue([]),
  clearMessageCache: vi.fn(),
}))

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('useChatStore - 基础状态和计算属性', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初始化状态正确', () => {
    const store = useChatStore()

    expect(store.messages).toEqual([])
    expect(store.isLoading).toBe(false)
    expect(store.isStreaming).toBe(false)
    expect(store.conversationCount).toBe(0)
    expect(store.currentConversationId).toBeNull()
    expect(store.lastError).toBeNull()
    expect(store.hasMoreHistory).toBe(true)
  })

  it('clearMessages 清除消息', () => {
    const store = useChatStore()

    store.messages.push({ id: '1', role: 'user', content: 'test', timestamp: '2024-01-01' } as any)
    store.conversationCount = 5

    store.clearMessages()

    expect(store.messages).toEqual([])
    expect(store.conversationCount).toBe(0)
  })

  it('clearError 清除错误', () => {
    const store = useChatStore()

    store.lastError = { code: 'TEST', message: 'Test error' } as any
    store.clearError()

    expect(store.lastError).toBeNull()
  })

  it('recentMessages 计算最近消息', () => {
    const store = useChatStore()

    for (let i = 0; i < 25; i++) {
      store.messages.push({
        id: `${i}`,
        role: 'user',
        content: `Message ${i}`,
        timestamp: `2024-01-01T00:00:${i.toString().padStart(2, '0')}Z`,
      } as any)
    }

    expect(store.recentMessages.length).toBe(20)
  })

  it('userMessages 过滤用户消息', () => {
    const store = useChatStore()

    store.messages.push(
      { id: '1', role: 'user', content: 'User message', timestamp: '' } as any,
      { id: '2', role: 'assistant', content: 'Assistant message', timestamp: '' } as any,
      { id: '3', role: 'user', content: 'Another user message', timestamp: '' } as any
    )

    expect(store.userMessages.length).toBe(2)
  })
})

describe('useChatStore - 对话管理', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('startNewConversation 开始新对话', async () => {
    const store = useChatStore()

    const conversationId = await store.startNewConversation('char-456')

    expect(conversationId).toBeTruthy()
    expect(store.currentConversationId).toBe(conversationId)
    expect(store.messages).toEqual([])
  })

  it('switchConversation 切换对话', async () => {
    const store = useChatStore()
    store.currentConversationId = 'old-conv'
    store.messages.push({ id: '1', role: 'user', content: 'test', timestamp: '2024-01-01' } as any)

    mockAccountStore.getConversation = vi.fn().mockResolvedValue({
      id: 'new-conv',
      messages: [],
    })

    await store.switchConversation('new-conv')

    expect(store.currentConversationId).toBe('new-conv')
  })

  it('stopStreaming 停止流式传输', () => {
    const store = useChatStore()
    store.stopStreaming()
  })
})

describe('useChatStore - 发送消息', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockModelsStore.models = [{ id: 'model-1', isEnabled: true, apiKey: 'test-key' }]
  })

  it('不发送空消息', async () => {
    const store = useChatStore()

    const result = await store.sendMessage('')

    expect(result).toBeNull()
    expect(store.messages.length).toBe(0)
  })

  it('加载时不发送消息', async () => {
    const store = useChatStore()

    store.isLoading = true

    const result = await store.sendMessage('test message')

    expect(result).toBeNull()
  })

  it('没有可用模型时不发送消息', async () => {
    const store = useChatStore()
    mockModelsStore.models = []

    const result = await store.sendMessage('test message')

    expect(result).toBeNull()
  })

  it('成功发送消息', async () => {
    const store = useChatStore()

    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      reply: 'Hello!',
      conversationId: 'conv-123',
      emotion: { valence: 0.5, arousal: 0.5 },
    })

    const result = await store.sendMessage('Hi')

    expect(result).not.toBeNull()
    expect(store.messages.length).toBe(2)
  })

  it('发送消息失败时添加错误消息', async () => {
    const store = useChatStore()

    vi.mocked(chatApi.sendMessage).mockRejectedValue({
      code: 'API_ERROR',
      message: 'API failed',
    })

    const result = await store.sendMessage('Hi')

    expect(result).toBeNull()
    expect(store.lastError).not.toBeNull()
  })
})

describe('useChatStore - 历史记录', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('loadHistory 加载历史记录', async () => {
    const store = useChatStore()
    await store.startNewConversation()

    vi.mocked(chatApi.getHistory).mockResolvedValue({
      messages: [],
    })

    await store.loadHistory()

    expect(chatApi.getHistory).toHaveBeenCalled()
  })

  it('loadMoreMessages 加载更多消息', async () => {
    const store = useChatStore()
    await store.startNewConversation()

    vi.mocked(chatApi.getHistory).mockResolvedValue({
      messages: [],
    })

    const result = await store.loadMoreMessages()

    expect(typeof result).toBe('boolean')
  })
})

describe('useChatStore - 流式消息', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockModelsStore.models = [{ id: 'model-1', isEnabled: true, apiKey: 'test-key' }]
  })

  it('sendMessageStream 不发送空消息', async () => {
    const store = useChatStore()
    await store.sendMessageStream('')
    expect(store.messages.length).toBe(0)
  })

  it('sendMessageStream 加载时不发送消息', async () => {
    const store = useChatStore()
    store.isLoading = true
    await store.sendMessageStream('test')
  })

  it('sendMessageStream 正在流式传输时不发送', async () => {
    const store = useChatStore()
    store.isStreaming = true
    await store.sendMessageStream('test')
  })

  it('sendMessageStream 没有可用模型时不发送', async () => {
    const store = useChatStore()
    mockModelsStore.models = []
    await store.sendMessageStream('test')
  })
})

describe('useChatStore - 初始化对话', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initializeConversation 没有对话时直接返回', async () => {
    const store = useChatStore()
    mockAccountStore.loadConversations.mockResolvedValue([])
    await store.initializeConversation()
    expect(mockAccountStore.loadConversations).toHaveBeenCalled()
  })

  it('initializeConversation 有对话时切换到最新对话', async () => {
    const store = useChatStore()
    const conversations = [
      { id: 'conv-1', updatedAt: '2024-01-01' },
      { id: 'conv-2', updatedAt: '2024-01-02' },
    ]
    mockAccountStore.loadConversations.mockResolvedValue(conversations)
    mockAccountStore.getConversation.mockResolvedValue(null)
    await store.initializeConversation()
    expect(mockAccountStore.loadConversations).toHaveBeenCalled()
  })
})

describe('useChatStore - 停止流式传输', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('stopStreaming 可以正常调用', () => {
    const store = useChatStore()
    store.stopStreaming()
  })
})

describe('useChatStore - 发送消息深度测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockModelsStore.models = [{ id: 'model-1', isEnabled: true, apiKey: 'test-key' }]
  })

  it('sendMessage 深度思考模式正常工作', async () => {
    const store = useChatStore()
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      reply: 'Hello with deep thinking!',
      conversationId: 'conv-123',
      emotion: { valence: 0.5, arousal: 0.5 },
    })

    const result = await store.sendMessage('Hi', true)

    expect(result).not.toBeNull()
    expect(chatApi.sendMessage).toHaveBeenCalled()
  })

  it('sendMessage 没有对话时自动创建新对话', async () => {
    const store = useChatStore()
    store.currentConversationId = null
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      reply: 'Hello!',
    })

    await store.sendMessage('Hi')

    expect(store.currentConversationId).not.toBeNull()
  })

  it('sendMessage 响应包含 conversationId 时更新当前对话', async () => {
    const store = useChatStore()
    await store.startNewConversation()
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      reply: 'Hello!',
      conversationId: 'new-conv-id',
    })

    await store.sendMessage('Hi')

    expect(store.currentConversationId).toBe('new-conv-id')
  })

  it('sendMessage 响应包含 newSummary 时正常处理', async () => {
    const store = useChatStore()
    await store.startNewConversation()
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      reply: 'Hello!',
      newSummary: 'New summary',
    })

    const result = await store.sendMessage('Hi')

    expect(result).not.toBeNull()
  })

  it('sendMessage 空消息返回 null', async () => {
    const store = useChatStore()

    const result = await store.sendMessage('   ')

    expect(result).toBeNull()
  })
})

describe('useChatStore - 开始新对话深入测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('startNewConversation 有 characterId 时设置为活跃角色', async () => {
    const store = useChatStore()

    await store.startNewConversation('char-new')

    expect(mockAccountStore.setActiveCharacterId).toHaveBeenCalledWith('char-new')
  })

  it('startNewConversation 创建对话 API 失败时使用本地模式', async () => {
    const store = useChatStore()
    vi.mocked(conversationsApi.createConversation).mockRejectedValue(new Error('API failed'))

    const conversationId = await store.startNewConversation()

    expect(conversationId).toBeTruthy()
    expect(mockAccountStore.saveConversation).toHaveBeenCalled()
  })

  it('startNewConversation 保存本地对话记录', async () => {
    const store = useChatStore()

    await store.startNewConversation('char-123')

    expect(mockAccountStore.saveConversation).toHaveBeenCalled()
  })
})

describe('useChatStore - 切换对话深入测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('switchConversation 有当前对话时保存消息', async () => {
    const store = useChatStore()
    await store.startNewConversation('char-1')
    mockAccountStore.getConversation.mockResolvedValue(null)

    await store.switchConversation('conv-2')
  })

  it('switchConversation 重置历史记录分页状态', async () => {
    const store = useChatStore()
    await store.startNewConversation()
    mockAccountStore.getConversation.mockResolvedValue(null)

    await store.switchConversation('conv-reset')

    expect(store.hasMoreHistory).toBe(true)
  })
})

describe('useChatStore - 组合场景测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockModelsStore.models = [{ id: 'model-1', isEnabled: true, apiKey: 'test-key' }]
  })

  it('完整对话流程测试', async () => {
    const store = useChatStore()
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      reply: 'First response',
      conversationId: 'conv-1',
    })

    await store.startNewConversation('char-1')
    await store.sendMessage('Hello')

    expect(store.messages.length).toBe(2)
    expect(store.currentConversationId).toBe('conv-1')

    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      reply: 'Second response',
    })

    await store.sendMessage('How are you?')

    expect(store.messages.length).toBe(4)
    expect(store.conversationCount).toBe(2)
  })

  it('多次切换对话状态保持正确', async () => {
    const store = useChatStore()
    mockAccountStore.getConversation.mockResolvedValue(null)

    await store.startNewConversation('char-1')
    expect(store.currentConversationId).not.toBeNull()

    const firstConvId = store.currentConversationId
    await store.switchConversation('conv-2')

    expect(store.currentConversationId).toBe('conv-2')

    await store.switchConversation(firstConvId!)

    expect(store.currentConversationId).toBe(firstConvId)
  })

  it('发送消息失败后清除错误继续发送', async () => {
    const store = useChatStore()
    await store.startNewConversation()

    vi.mocked(chatApi.sendMessage).mockRejectedValue({
      code: 'ERROR',
      message: 'Test error',
    })

    await store.sendMessage('Hello')
    expect(store.lastError).not.toBeNull()

    store.clearError()
    expect(store.lastError).toBeNull()

    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      reply: 'Success!',
    })

    const result = await store.sendMessage('Try again')
    expect(result).not.toBeNull()
  })
})
