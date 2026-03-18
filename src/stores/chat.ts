import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatRequest, ChatResponse } from '@/types'
import { chatApi } from '@/api/chat'
import type { ApiError } from '@/api/http-client'
import dayjs from 'dayjs'
import { logger } from '@/utils/logger'

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
  const pageSize = 20

  const recentMessages = computed(() => {
    return messages.value.slice(-20)
  })

  const userMessages = computed(() => {
    return messages.value.filter(m => m.role === 'user')
  })

  async function sendMessage(content: string): Promise<ChatResponse | null> {
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

  async function loadHistory(): Promise<void> {
    try {
      const history = await chatApi.getHistory(currentUserId.value, 50)
      messages.value = history.messages
    } catch (error) {
      logger.error('ChatStore', 'Failed to load history', error)
    }
  }

  async function loadMoreMessages(): Promise<boolean> {
    if (!hasMoreHistory.value) return false

    try {
      historyPage.value++
      const offset = historyPage.value * pageSize
      const history = await chatApi.getHistory(currentUserId.value, pageSize, offset)

      if (history.messages.length === 0) {
        hasMoreHistory.value = false
        return false
      }

      const olderMessages = history.messages.reverse()
      messages.value = [...olderMessages, ...messages.value]

      if (history.messages.length < pageSize) {
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
