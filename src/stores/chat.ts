import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatRequest, ChatResponse, EmotionData } from '@/types'
import { chatApi } from '@/api/chat'
import { useAccountStore, type AccountConversation } from './account'
import { useModelsStore } from './models'
import type { ApiError } from '@/api/http-client'
import dayjs from 'dayjs'
import { logger } from '@/utils/logger'
import { clearMessageCache, saveToStorage, loadFromStorage } from '@/utils/local-storage'
import { sortMessages, mergeMessageHistory, dedupeMessagesById } from '@/utils/message'
import { generateConversationId, createTypewriterBuffer } from '@/utils'
import type { TypewriterBuffer } from '@/utils'

const INITIAL_LOAD_LIMIT = 10
const LOAD_MORE_LIMIT = 20
const TEMPERATURE = 1.00
const TYPEWRITER_BUFFER_THRESHOLD = 20
const TYPEWRITER_CHARS_PER_SECOND = 30

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
  const typewriterBuffer = ref<TypewriterBuffer | null>(null)
  const typewriterRenderCount = ref(0)

  function ensureCurrentUserId(): string {
    if (currentUserId.value && currentUserId.value !== 'default') {
      return currentUserId.value
    }

    const accountStore = useAccountStore()
    const accountId = accountStore.currentAccountId
    if (!accountId) {
      throw new Error('当前账号未初始化，无法发送消息')
    }

    currentUserId.value = accountId
    return accountId
  }

  function checkEnabledModels(): boolean {
    const modelsStore = useModelsStore()
    const enabledModels = modelsStore.models.filter(m => m.isEnabled && m.apiKey)
    if (enabledModels.length === 0) {
      logger.error('ChatStore', 'No available models to send message')
      return false
    }
    return true
  }

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

  function createMessage(
    role: 'user' | 'assistant',
    content: string,
    emotion?: EmotionData
  ): ChatMessage {
    const timestamp = dayjs().toISOString()
    return {
      id: `${role}-${Date.now()}`,
      role,
      content: content.trim(),
      timestamp,
      emotion,
    }
  }

  function createErrorMessage(): ChatMessage {
    return createMessage('assistant', '抱歉，我遇到了一些问题，请稍后再试。')
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

  function clearTypewriterBuffer(): void {
    if (typewriterBuffer.value) {
      typewriterBuffer.value.stop()
      typewriterBuffer.value = null
    }
  }

  function updateLastAssistantMessage(content: string): void {
    if (messages.value.length === 0) return
    const lastMessage = messages.value[messages.value.length - 1]
    if (lastMessage.role === 'assistant') {
      lastMessage.content = content
    }
  }

  async function initializeConversation(): Promise<void> {
    const accountStore = useAccountStore()
    const conversations = await accountStore.loadConversations()

    if (conversations.length === 0) return

    const typedConversations = conversations as Array<{ id: string; updatedAt?: string }>
    const latestConv = typedConversations.sort(
      (a, b) => new Date(b.updatedAt || 0).getTime() - new Date(a.updatedAt || 0).getTime()
    )[0]

    await switchConversation(latestConv.id)
  }

  const recentMessages = computed(() => messages.value.slice(-20))
  const userMessages = computed(() => messages.value.filter(m => m.role === 'user'))

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
        messages.value = dedupeMessagesById(history.messages)
        saveCurrentConversationMessages()
      } catch (error) {
        logger.error('ChatStore', 'Failed to load conversation history', error)
      }
    } else {
      messages.value = dedupeMessagesById(messages.value)
    }

    historyPage.value = 0
    hasMoreHistory.value = true

    logger.info('ChatStore', 'Switched to conversation', { conversationId })
  }

  async function startNewConversation(characterId?: string): Promise<string> {
    if (currentConversationId.value) {
      saveCurrentConversationMessages()
    }

    resetConversationState()

    const newId = generateConversationId()
    currentConversationId.value = newId

    const accountStore = useAccountStore()
    ensureCurrentUserId()
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

  async function buildChatRequest(content: string, deepThinking: boolean): Promise<ChatRequest> {
    const accountStore = useAccountStore()
    const characterId = accountStore.currentConfig?.activeCharacterId ?? undefined
    const userId = ensureCurrentUserId()

    return {
      userId,
      conversationId: currentConversationId.value ?? undefined,
      message: content.trim(),
      temperature: TEMPERATURE,
      deepThinking,
      ...(characterId ? { characterId } : {}),
    }
  }

  async function updateConversationMetadata(content: string, characterId?: string): Promise<void> {
    const accountStore = useAccountStore()
    const conv = await accountStore.getConversation(currentConversationId.value!)
    const title = content.slice(0, 30) + (content.length > 30 ? '...' : '')

    if (!conv) {
      await accountStore.saveConversation({
        id: currentConversationId.value!,
        characterId,
        title,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      })
    } else {
      const convData = conv as AccountConversation
      convData.updatedAt = new Date().toISOString()
      if (!convData.title) {
        convData.title = title
      }
      await accountStore.saveConversation(convData)
    }
  }

  async function sendMessage(content: string, deepThinking = false): Promise<ChatResponse | null> {
    if (!content.trim() || isLoading.value) return null
    if (!checkEnabledModels()) return null

    lastError.value = null

    if (!currentConversationId.value) {
      await startNewConversation()
    }

    const userMessage = createMessage('user', content)
    messages.value.push(userMessage)
    isLoading.value = true

    try {
      if (deepThinking) {
        logger.info('ChatStore', 'Sending with deep thinking enabled')
      }

      const request = await buildChatRequest(content, deepThinking)
      const response: ChatResponse = await chatApi.sendMessage(request)

      if (response.conversationId) {
        currentConversationId.value = response.conversationId
      }

      const assistantMessage = createMessage('assistant', response.reply, response.emotion)
      messages.value.push(assistantMessage)
      conversationCount.value++
      saveCurrentConversationMessages()

      await updateConversationMetadata(content, request.characterId)

      if (response.newSummary) {
        logger.info('ChatStore', 'Memory summary updated', { summary: response.newSummary })
      }

      return response
    } catch (error) {
      lastError.value = error as ApiError
      messages.value.push(createErrorMessage())
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

    typewriterBuffer.value = createTypewriterBuffer({
      bufferThreshold: TYPEWRITER_BUFFER_THRESHOLD,
      charsPerSecond: TYPEWRITER_CHARS_PER_SECOND,
    })

    typewriterBuffer.value.onRender(text => {
      streamingContent.value = text
      updateLastAssistantMessage(text)
    })

    typewriterBuffer.value.onProgress(() => {
      typewriterRenderCount.value++
    })
  }

  function createUserAndAssistantMessages(content: string): void {
    messages.value.push(createMessage('user', content))
    messages.value.push(createMessage('assistant', ''))
  }

  async function fetchStreamResponse(
    content: string
  ): Promise<ReadableStreamDefaultReader<Uint8Array> | null> {
    const accountStore = useAccountStore()
    const characterId = accountStore.currentConfig?.activeCharacterId
    const userId = ensureCurrentUserId()
    const accessToken = localStorage.getItem('yumi_access_token')

    const params = new URLSearchParams({
      userId,
      message: content.trim(),
      temperature: String(TEMPERATURE),
    })
    if (currentConversationId.value) {
      params.set('conversationId', currentConversationId.value)
    }
    if (characterId) {
      params.set('characterId', characterId)
    }

    const response = await fetch(`/api/chat/stream?${params}`, {
      signal: abortController.value!.signal,
      headers: {
        Accept: 'text/event-stream',
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
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
      if (messages.value.length > 0) {
        const lastMessage = messages.value[messages.value.length - 1]
        if (lastMessage.role === 'assistant' && parsed.emotion) {
          lastMessage.emotion = parsed.emotion
        }
      }

      if (typewriterBuffer.value) {
        typewriterBuffer.value.endStream()
      }

      conversationCount.value++
      saveCurrentConversationMessages()
      return false
    }

    if (parsed.content) {
      if (typewriterBuffer.value) {
        typewriterBuffer.value.pushCharacters(parsed.content)
      } else {
        streamingContent.value += parsed.content
        updateLastAssistantMessage(streamingContent.value)
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
    if (!checkEnabledModels()) return

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
      clearTypewriterBuffer()
    }
  }

  function stopStreaming(): void {
    if (abortController.value) {
      abortController.value.abort()
    }
    clearTypewriterBuffer()
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
        ensureCurrentUserId(),
        limit,
        0,
        currentConversationId.value
      )
      messages.value = dedupeMessagesById(history.messages)
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
        ensureCurrentUserId(),
        LOAD_MORE_LIMIT,
        offset,
        currentConversationId.value
      )

      if (history.messages.length === 0) {
        hasMoreHistory.value = false
        return false
      }

      messages.value = mergeMessageHistory(history.messages, messages.value)

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

  function clearMessages(): void {
    resetConversationState()
    clearMessageCache()
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
    typewriterRenderCount,
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
