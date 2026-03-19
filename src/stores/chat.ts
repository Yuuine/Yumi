import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatRequest, ChatResponse } from '@/types'
import { chatApi } from '@/api/chat'
import type { ApiError } from '@/api/http-client'
import dayjs from 'dayjs'
import { logger } from '@/utils/logger'
import { cacheMessages, getCachedMessages, clearAllCache } from '@/utils/local-storage'

// 懒加载参数配置
const INITIAL_LOAD_LIMIT = 10
const LOAD_MORE_LIMIT = 20

function stableSortMessages(msgs: ChatMessage[]): ChatMessage[] {
  return [...msgs].sort((a, b) => {
    const timeDiff = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    if (timeDiff !== 0) return timeDiff
    if (a.role !== b.role) {
      return a.role === 'user' ? -1 : 1
    }
    return a.id.localeCompare(b.id)
  })
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const currentUserId = ref('default')
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
      const request: ChatRequest = {
        userId: currentUserId.value,
        message: content.trim(),
        temperature: 0.85,
        deepThinking,
      }

      if (deepThinking) {
        logger.info('ChatStore', 'Sending with deep thinking enabled')
      }

      const response: ChatResponse = await chatApi.sendMessage(request)

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

  async function sendMessageStream(content: string): Promise<void> {
    if (!content.trim() || isLoading.value || isStreaming.value) return

    lastError.value = null
    streamingContent.value = ''
    isStreaming.value = true
    abortController.value = new AbortController()

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

    try {
      const params = new URLSearchParams({
        userId: currentUserId.value,
        message: content.trim(),
        temperature: '0.85',
      })

      const response = await fetch(`/api/chat/stream?${params}`, {
        signal: abortController.value.signal,
        headers: {
          Accept: 'text/event-stream',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            try {
              const parsed = JSON.parse(data)

              if (parsed.error) {
                lastError.value = { code: 'STREAM_ERROR', message: parsed.error }
                break
              }

              if (parsed.done) {
                const lastMessage = messages.value[messages.value.length - 1]
                if (lastMessage.role === 'assistant' && parsed.emotion) {
                  lastMessage.emotion = parsed.emotion
                }
                conversationCount.value++
                continue
              }

              if (parsed.content) {
                streamingContent.value += parsed.content
                const lastMessage = messages.value[messages.value.length - 1]
                if (lastMessage.role === 'assistant') {
                  lastMessage.content = streamingContent.value
                }
              }
            } catch {
              // Ignore parse errors for incomplete JSON
            }
          }
        }
      }
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        // User cancelled, do nothing
        return
      }

      const apiError = error as ApiError
      lastError.value = apiError

      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage.role === 'assistant' && !lastMessage.content) {
        lastMessage.content = '抱歉，我遇到了一些问题，请稍后再试。'
      }
    } finally {
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
      messages.value = stableSortMessages(cachedMessages)
      logger.info('ChatStore', 'Loaded cached messages', { count: cachedMessages.length })
    }

    try {
      const history = await chatApi.getHistory(currentUserId.value, limit)
      messages.value = stableSortMessages(history.messages)
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

      messages.value = stableSortMessages([...history.messages, ...messages.value])

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
    conversationCount.value = 0
    lastError.value = null
    streamingContent.value = ''
    historyPage.value = 0
    hasMoreHistory.value = true
    clearAllCache()
  }

  function clearError(): void {
    lastError.value = null
  }

  return {
    messages,
    isLoading,
    currentUserId,
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
    clearError,
  }
})
