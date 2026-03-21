import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatRequest, ChatResponse, EmotionData } from '@/types'
import { chatApi } from '@/api/chat'
import { useAccountStore } from './account'
import type { ApiError } from '@/api/http-client'
import dayjs from 'dayjs'
import { logger } from '@/utils/logger'
import { cacheMessages, getCachedMessages, clearAllCache } from '@/utils/local-storage'
import { sortMessages } from '@/utils/message'

const INITIAL_LOAD_LIMIT = 10
const LOAD_MORE_LIMIT = 20

/**
 * 流式响应解析结果
 */
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

  const recentMessages = computed(() => {
    return messages.value.slice(-20)
  })

  const userMessages = computed(() => {
    return messages.value.filter(m => m.role === 'user')
  })

  async function sendMessage(content: string, deepThinking = false): Promise<ChatResponse | null> {
    if (!content.trim() || isLoading.value) return null

    lastError.value = null

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: dayjs().toISOString(),
    }

    messages.value.push(userMessage)
    isLoading.value = true

    try {
      const accountStore = useAccountStore()
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
      cacheMessages(messages.value)

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

  /**
   * 初始化流式传输状态
   */
  function initializeStreamState(): void {
    lastError.value = null
    streamingContent.value = ''
    isStreaming.value = true
    abortController.value = new AbortController()
  }

  /**
   * 创建用户消息和助手消息并添加到消息列表
   * @param content - 用户消息内容
   */
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

  /**
   * 发起流式请求并返回 ReadableStream reader
   * @param content - 用户消息内容
   * @returns ReadableStream reader 或 null
   */
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

  /**
   * 解析单行流式数据
   * @param line - SSE 数据行
   */
  function parseStreamLine(line: string): void {
    if (!line.startsWith('data: ')) return

    const data = line.slice(6)
    try {
      const parsed = JSON.parse(data) as StreamParsedData
      handleStreamData(parsed)
    } catch {
      // 忽略不完整 JSON 的解析错误
    }
  }

  /**
   * 读取并处理流式响应
   * @param reader - ReadableStream reader
   */
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

  /**
   * 处理流式传输错误
   * @param error - 错误对象
   */
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

  /**
   * 发送流式消息
   * @param content - 用户消息内容
   */
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
      if (messages.value.length > 0) {
        cacheMessages(messages.value)
      }
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
    const cachedMessages = getCachedMessages<ChatMessage>()
    if (cachedMessages.length > 0) {
      messages.value = sortMessages(cachedMessages)
      logger.info('ChatStore', 'Loaded cached messages', { count: cachedMessages.length })
    }

    try {
      const history = await chatApi.getHistory(currentUserId.value, limit)
      messages.value = sortMessages(history.messages)
      cacheMessages(messages.value)

      hasMoreHistory.value = history.messages.length >= limit
    } catch (error) {
      logger.error('ChatStore', 'Failed to load history', error)
    }
  }

  async function loadMoreMessages(): Promise<boolean> {
    if (!hasMoreHistory.value) return false

    try {
      historyPage.value++
      // 计算偏移量：初始加载的消息数 + 已加载的页数 * 每页消息数
      const offset = INITIAL_LOAD_LIMIT + (historyPage.value - 1) * LOAD_MORE_LIMIT
      const history = await chatApi.getHistory(currentUserId.value, LOAD_MORE_LIMIT, offset)

      if (history.messages.length === 0) {
        hasMoreHistory.value = false
        return false
      }

      messages.value = sortMessages([...history.messages, ...messages.value])

      // 如果返回的消息数少于请求的数量，说明没有更多历史消息
      if (history.messages.length < LOAD_MORE_LIMIT) {
        hasMoreHistory.value = false
      }

      return hasMoreHistory.value
    } catch (error) {
      logger.error('ChatStore', 'Failed to load more messages', error)
      historyPage.value--
      return false
    }
  }

  function clearMessages(): void {
    messages.value = []
    currentConversationId.value = null
    conversationCount.value = 0
    lastError.value = null
    streamingContent.value = ''
    historyPage.value = 0
    hasMoreHistory.value = true
    clearAllCache()
  }

  function startNewConversation(): void {
    messages.value = []
    currentConversationId.value = null
    conversationCount.value = 0
    lastError.value = null
    streamingContent.value = ''
    historyPage.value = 0
    hasMoreHistory.value = true
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
    clearError,
  }
})
