import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatRequest, ChatResponse, EmotionData } from '@/types'
import { chatApi } from '@/api/chat'
import { useAccountStore, type AccountConversation } from './account'
import type { ApiError } from '@/api/http-client'
import dayjs from 'dayjs'
import { logger } from '@/utils/logger'
import { clearAllCache, saveToStorage, loadFromStorage } from '@/utils/local-storage'
import { sortMessages } from '@/utils/message'
import { generateConversationId } from '@/utils'

const INITIAL_LOAD_LIMIT = 10
const LOAD_MORE_LIMIT = 20

const KEYS = {
  MESSAGES_PREFIX: 'yumi_conversation_messages_',
} as const

interface StreamParsedData {
  error?: string
  done?: boolean
  emotion?: EmotionData
  content?: string
  conversationId?: string
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const currentUserId = ref('default')
  const currentConversationId = ref<string | null>(null)
  const conversationCount = ref(0)
  const lastError = ref<ApiError | null>(null)
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const abortController = ref<AbortController | null>(null)
  const historyPage = ref(0)
  const hasMoreHistory = ref(true)

  async function initializeConversation(): Promise<void> {
    const accountStore = useAccountStore()
    const conversations = await accountStore.loadConversations()
    
    if (conversations.length > 0) {
      const typedConversations = conversations as Array<{ id: string; updatedAt?: string }>
      const latestConv = typedConversations.sort((a, b) => 
        new Date(b.updatedAt || 0).getTime() - new Date(a.updatedAt || 0).getTime()
      )[0]
      
      await switchConversation(latestConv.id)
    }
  }

  const recentMessages = computed(() => {
    return messages.value.slice(-20)
  })

  const userMessages = computed(() => {
    return messages.value.filter(m => m.role === 'user')
  })

  function getConversationStorageKey(conversationId: string): string {
    return `${KEYS.MESSAGES_PREFIX}${conversationId}`
  }

  function saveCurrentConversationMessages(): void {
    if (currentConversationId.value) {
      saveToStorage(getConversationStorageKey(currentConversationId.value), messages.value)
    }
  }

  function loadConversationMessages(conversationId: string): ChatMessage[] {
    return loadFromStorage<ChatMessage[]>(getConversationStorageKey(conversationId), [])
  }

  async function switchConversation(conversationId: string): Promise<void> {
    if (currentConversationId.value) {
      saveCurrentConversationMessages()
    }

    currentConversationId.value = conversationId
    messages.value = loadConversationMessages(conversationId)

    if (messages.value.length === 0) {
      try {
        const history = await chatApi.getHistory(
          currentUserId.value,
          INITIAL_LOAD_LIMIT,
          0,
          conversationId
        )
        messages.value = sortMessages(history.messages)
        saveCurrentConversationMessages()
      } catch (error) {
        logger.error('ChatStore', 'Failed to load conversation history', error)
      }
    }

    historyPage.value = 0
    hasMoreHistory.value = true

    logger.info('ChatStore', 'Switched to conversation', { conversationId })
  }

  async function startNewConversation(characterId?: string): Promise<string> {
    if (currentConversationId.value) {
      saveCurrentConversationMessages()
    }

    const newId = generateConversationId()
    currentConversationId.value = newId
    messages.value = []
    conversationCount.value = 0
    lastError.value = null
    streamingContent.value = ''
    historyPage.value = 0
    hasMoreHistory.value = true

    const accountStore = useAccountStore()
    const targetCharacterId =
      characterId ?? accountStore.currentConfig?.activeCharacterId ?? undefined

    if (characterId) {
      await accountStore.setActiveCharacterId(characterId)
    }

    await accountStore.saveConversation({
      id: newId,
      characterId: targetCharacterId,
      title: '新对话',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    })

    logger.info('ChatStore', 'Started new conversation', {
      conversationId: newId,
      characterId: targetCharacterId,
    })
    return newId
  }

  async function sendMessage(content: string, deepThinking = false): Promise<ChatResponse | null> {
    if (!content.trim() || isLoading.value) return null

    lastError.value = null

    const accountStore = useAccountStore()

    if (!currentConversationId.value) {
      await startNewConversation()
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: dayjs().toISOString(),
    }

    messages.value.push(userMessage)
    isLoading.value = true

    try {
      const characterId = accountStore.currentConfig?.activeCharacterId ?? undefined

      const request: ChatRequest = {
        userId: currentUserId.value,
        conversationId: currentConversationId.value ?? undefined,
        message: content.trim(),
        temperature: 0.85,
        deepThinking,
        ...(characterId ? { characterId } : {}),
      }

      if (deepThinking) {
        logger.info('ChatStore', 'Sending with deep thinking enabled')
      }

      const response: ChatResponse = await chatApi.sendMessage(request)

      if (response.conversationId) {
        currentConversationId.value = response.conversationId
      }

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.reply,
        timestamp: dayjs().toISOString(),
        emotion: response.emotion,
      }

      messages.value.push(assistantMessage)
      conversationCount.value++
      saveCurrentConversationMessages()

      const conv = await accountStore.getConversation(currentConversationId.value!)
      if (!conv) {
        await accountStore.saveConversation({
          id: currentConversationId.value!,
          characterId,
          title: content.slice(0, 30) + (content.length > 30 ? '...' : ''),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        })
      } else {
        const convData = conv as AccountConversation
        convData.updatedAt = new Date().toISOString()
        if (!convData.title) {
          convData.title = content.slice(0, 30) + (content.length > 30 ? '...' : '')
        }
        await accountStore.saveConversation(convData)
      }

      if (response.newSummary) {
        logger.info('ChatStore', 'Memory summary updated', { summary: response.newSummary })
      }

      return response
    } catch (error) {
      const apiError = error as ApiError
      lastError.value = apiError

      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '抱歉，我遇到了一些问题，请稍后再试。',
        timestamp: dayjs().toISOString(),
      }
      messages.value.push(errorMessage)

      return null
    } finally {
      isLoading.value = false
    }
  }

  function initializeStreamState(): void {
    lastError.value = null
    streamingContent.value = ''
    isStreaming.value = true
    abortController.value = new AbortController()
  }

  function createUserAndAssistantMessages(content: string): void {
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: dayjs().toISOString(),
    }
    messages.value.push(userMessage)

    const assistantMessage: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: dayjs().toISOString(),
    }
    messages.value.push(assistantMessage)
  }

  async function fetchStreamResponse(
    content: string
  ): Promise<ReadableStreamDefaultReader<Uint8Array> | null> {
    const accountStore = useAccountStore()
    const characterId = accountStore.currentConfig?.activeCharacterId

    const params = new URLSearchParams({
      userId: currentUserId.value,
      message: content.trim(),
      temperature: '0.85',
    })
    if (currentConversationId.value) {
      params.set('conversationId', currentConversationId.value)
    }
    if (characterId) {
      params.set('characterId', characterId)
    }

    const response = await fetch(`/api/chat/stream?${params}`, {
      signal: abortController.value!.signal,
      headers: { Accept: 'text/event-stream' },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    return reader
  }

  function handleStreamData(parsed: StreamParsedData): boolean {
    if (parsed.error) {
      lastError.value = { code: 'STREAM_ERROR', message: parsed.error }
      return true
    }

    if (parsed.done) {
      if (parsed.conversationId) {
        currentConversationId.value = parsed.conversationId
      }
      if (messages.value.length === 0) return false
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage.role === 'assistant' && parsed.emotion) {
        lastMessage.emotion = parsed.emotion
      }
      conversationCount.value++
      saveCurrentConversationMessages()
      return false
    }

    if (parsed.content) {
      streamingContent.value += parsed.content
      if (messages.value.length === 0) return false
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage.role === 'assistant') {
        lastMessage.content = streamingContent.value
      }
    }

    return false
  }

  function parseStreamLine(line: string): void {
    if (!line.startsWith('data: ')) return

    const data = line.slice(6)
    try {
      const parsed = JSON.parse(data) as StreamParsedData
      handleStreamData(parsed)
    } catch (error) {
      logger.debug('ChatStore', 'Failed to parse stream line', { error })
    }
  }

  async function processStreamReader(
    reader: ReadableStreamDefaultReader<Uint8Array>
  ): Promise<void> {
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        parseStreamLine(line)
        if (lastError.value) {
          return
        }
      }
    }

    const remaining = buffer.trim()
    if (remaining) {
      parseStreamLine(remaining)
    }
  }

  function handleStreamError(error: unknown): void {
    if ((error as Error).name === 'AbortError') {
      return
    }

    lastError.value = error as ApiError
    if (messages.value.length === 0) return
    const lastMessage = messages.value[messages.value.length - 1]
    if (lastMessage.role === 'assistant' && !lastMessage.content) {
      lastMessage.content = '抱歉，我遇到了一些问题，请稍后再试。'
    }
  }

  async function sendMessageStream(content: string): Promise<void> {
    if (!content.trim() || isLoading.value || isStreaming.value) return

    initializeStreamState()
    createUserAndAssistantMessages(content)

    try {
      const reader = await fetchStreamResponse(content)
      if (reader) {
        await processStreamReader(reader)
      }
    } catch (error) {
      handleStreamError(error)
    } finally {
      saveCurrentConversationMessages()
      isStreaming.value = false
      abortController.value = null
    }
  }

  function stopStreaming(): void {
    if (abortController.value) {
      abortController.value.abort()
    }
  }

  async function loadHistory(limit = INITIAL_LOAD_LIMIT): Promise<void> {
    if (!currentConversationId.value) {
      return
    }

    const cachedMessages = loadConversationMessages(currentConversationId.value)
    if (cachedMessages.length > 0) {
      messages.value = sortMessages(cachedMessages)
      logger.info('ChatStore', 'Loaded cached messages for conversation', {
        conversationId: currentConversationId.value,
        count: cachedMessages.length,
      })
      return
    }

    try {
      const history = await chatApi.getHistory(
        currentUserId.value,
        limit,
        0,
        currentConversationId.value
      )
      messages.value = sortMessages(history.messages)
      saveCurrentConversationMessages()

      hasMoreHistory.value = history.messages.length >= limit
    } catch (error) {
      logger.error('ChatStore', 'Failed to load history', error)
    }
  }

  async function loadMoreMessages(): Promise<boolean> {
    if (!hasMoreHistory.value || !currentConversationId.value) return false

    try {
      historyPage.value++
      const offset = INITIAL_LOAD_LIMIT + (historyPage.value - 1) * LOAD_MORE_LIMIT
      const history = await chatApi.getHistory(
        currentUserId.value,
        LOAD_MORE_LIMIT,
        offset,
        currentConversationId.value
      )

      if (history.messages.length === 0) {
        hasMoreHistory.value = false
        return false
      }

      messages.value = sortMessages([...history.messages, ...messages.value])

      if (history.messages.length < LOAD_MORE_LIMIT) {
        hasMoreHistory.value = false
      }

      saveCurrentConversationMessages()
      return hasMoreHistory.value
    } catch (error) {
      logger.error('ChatStore', 'Failed to load more messages', error)
      historyPage.value--
      return false
    }
  }

  function resetConversationState(): void {
    messages.value = []
    currentConversationId.value = null
    conversationCount.value = 0
    lastError.value = null
    streamingContent.value = ''
    historyPage.value = 0
    hasMoreHistory.value = true
  }

  function clearMessages(): void {
    resetConversationState()
    clearAllCache()
  }

  function clearError(): void {
    lastError.value = null
  }

  return {
    messages,
    isLoading,
    currentUserId,
    currentConversationId,
    conversationCount,
    lastError,
    isStreaming,
    streamingContent,
    recentMessages,
    userMessages,
    hasMoreHistory,
    sendMessage,
    sendMessageStream,
    stopStreaming,
    loadHistory,
    loadMoreMessages,
    clearMessages,
    startNewConversation,
    switchConversation,
    clearError,
    initializeConversation,
  }
})
