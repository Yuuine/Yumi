<template>
  <div class="message-list" ref="containerRef" @scroll="handleScroll">
    <div ref="wrapperRef" class="messages-wrapper">
      <div v-if="isLoadingMore" class="loading-indicator">
        <IconSpinner class="spinner" />
        <span>加载历史消息...</span>
      </div>

      <div v-if="!hasMoreHistory && displayMessages.length > 0" class="no-more-indicator">
        <span>没有更多历史消息</span>
      </div>

      <MessageItem
        v-for="message in displayMessages"
        :key="message.id"
        :message="message"
        :data-message-id="message.id"
        class="message-item"
        @copy-content="handleCopy"
      />

      <div v-if="displayMessages.length === 0 && !isLoadingMore" class="empty-state">
        <span>暂无消息</span>
      </div>
    </div>

    <ScrollToBottom :visible="showScrollButton" @click="onScrollToBottomClick" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '@/stores'
import type { ChatMessage } from '@/types'
import MessageItem from './MessageItem.vue'
import ScrollToBottom from './ScrollToBottom.vue'
import { IconSpinner } from '@/components/icons'

interface Props {
  messages?: ChatMessage[]
}

const props = withDefaults(defineProps<Props>(), {
  messages: () => [],
})

const emit = defineEmits<{
  'copy-content': [content: string]
  loadMore: []
  scrollStateChange: [isAtBottom: boolean]
}>()

const chatStore = useChatStore()
const containerRef = ref<HTMLElement | null>(null)
const wrapperRef = ref<HTMLElement | null>(null)

let resizeObserver: ResizeObserver | null = null

const displayMessages = ref<ChatMessage[]>([])
const isLoadingMore = ref(false)
const hasMoreHistory = ref(true)
const isInternalUpdate = ref(false)
const isInitialLoad = ref(true)
const scrollDebounceTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const showScrollButton = ref(false)

const SCROLL_THRESHOLD = 150
const DEBOUNCE_DELAY = 100
const BOTTOM_THRESHOLD = 50

function isAtBottom(): boolean {
  if (!containerRef.value) return true
  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  return scrollHeight - scrollTop - clientHeight < BOTTOM_THRESHOLD
}

function scrollToBottom(): void {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  })
}

function beginStickyFollow(): void {}

function endStickyFollow(): void {}

async function completeStickyFollowSession(): Promise<void> {
  await nextTick()
  scrollToBottom()
}

function scrollToBottomInstant(): void {
  scrollToBottom()
}

function scrollToBottomSmooth(): void {
  scrollToBottom()
}

function onScrollToBottomClick(): void {
  scrollToBottom()
}

watch(
  () => chatStore.currentConversationId,
  (id, prev) => {
    if (id === prev) return
    if (prev === undefined) return
    isInitialLoad.value = true
  }
)

onMounted(() => {
  nextTick(() => {
    const wrap = wrapperRef.value
    if (!wrap || typeof ResizeObserver === 'undefined') return
    resizeObserver = new ResizeObserver(() => {
      if (isAtBottom()) {
        scrollToBottom()
      }
    })
    resizeObserver.observe(wrap)
  })
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  if (scrollDebounceTimer.value) {
    clearTimeout(scrollDebounceTimer.value)
  }
})

watch(
  () => props.messages,
  (newMessages, oldMessages) => {
    const prevLength = oldMessages?.length || 0
    const newLength = newMessages.length

    if (isInitialLoad.value) {
      displayMessages.value = [...newMessages]
      isInitialLoad.value = false
      nextTick(() => {
        scrollToBottom()
        emit('scrollStateChange', true)
      })
      return
    }

    if (isInternalUpdate.value) {
      displayMessages.value = [...newMessages]
      isInternalUpdate.value = false
      return
    }

    if (newLength > prevLength) {
      displayMessages.value = [...newMessages]
      if (isAtBottom()) {
        nextTick(() => {
          scrollToBottom()
          emit('scrollStateChange', true)
        })
      }
      return
    }

    if (newLength === prevLength && oldMessages) {
      const isUpdatingLastMessage =
        newLength > 0 &&
        oldMessages[newMessages.length - 1]?.id === newMessages[newMessages.length - 1]?.id &&
        oldMessages[newMessages.length - 1]?.content !==
          newMessages[newMessages.length - 1]?.content

      displayMessages.value = [...newMessages]

      if (isUpdatingLastMessage && isAtBottom()) {
        nextTick(() => {
          scrollToBottom()
          emit('scrollStateChange', true)
        })
      }
    } else {
      displayMessages.value = [...newMessages]
    }
  },
  { deep: true, immediate: true }
)

function getFirstVisibleMessageId(): string | null {
  if (!containerRef.value) return null
  const container = containerRef.value
  const messageElements = container.querySelectorAll('.message-item')

  for (const el of messageElements) {
    const rect = el.getBoundingClientRect()
    const containerRect = container.getBoundingClientRect()
    if (rect.top >= containerRect.top && rect.bottom <= containerRect.bottom) {
      return el.getAttribute('data-message-id')
    }
  }
  return null
}

function scrollToMessage(messageId: string | null) {
  if (!messageId || !containerRef.value) return
  const messageEl = containerRef.value.querySelector(`[data-message-id="${messageId}"]`)
  if (messageEl) {
    messageEl.scrollIntoView({ block: 'start', behavior: 'auto' })
  }
}

function handleScroll() {
  if (!containerRef.value) return

  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  const currentIsAtBottom = distanceFromBottom < BOTTOM_THRESHOLD

  showScrollButton.value = !currentIsAtBottom

  emit('scrollStateChange', currentIsAtBottom)

  if (scrollDebounceTimer.value) {
    clearTimeout(scrollDebounceTimer.value)
  }

  scrollDebounceTimer.value = setTimeout(() => {
    if (!containerRef.value) return

    const currentScrollTop = containerRef.value.scrollTop

    if (currentScrollTop < SCROLL_THRESHOLD && !isLoadingMore.value && hasMoreHistory.value) {
      loadMoreHistory()
    }
  }, DEBOUNCE_DELAY)
}

async function loadMoreHistory() {
  if (isLoadingMore.value || !hasMoreHistory.value) return

  isLoadingMore.value = true

  const firstVisibleId = getFirstVisibleMessageId()

  isInternalUpdate.value = true
  emit('loadMore')

  await waitForDomUpdate()

  nextTick(() => {
    scrollToMessage(firstVisibleId)
    isLoadingMore.value = false
  })
}

function waitForDomUpdate(): Promise<void> {
  return new Promise(resolve => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve())
    })
  })
}

function handleCopy(content: string) {
  emit('copy-content', content)
}

function setHasMoreHistory(value: boolean) {
  hasMoreHistory.value = value
}

function setLoadingMore(value: boolean) {
  isLoadingMore.value = value
}

function getScrollProgress(): number {
  if (!containerRef.value) return 0
  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  const maxScroll = scrollHeight - clientHeight
  return maxScroll > 0 ? (scrollTop / maxScroll) * 100 : 100
}

function getMessageProgress(): number {
  if (!containerRef.value || displayMessages.value.length === 0) return 0
  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  const messageHeight = scrollHeight / displayMessages.value.length
  const visibleMessages = Math.ceil(clientHeight / messageHeight)
  const currentMessageIndex = Math.floor(scrollTop / messageHeight)
  return ((currentMessageIndex + visibleMessages) / displayMessages.value.length) * 100
}

defineExpose({
  /** 瞬时到底（兼容旧调用：切换会话、挂载） */
  scrollToBottom: scrollToBottomInstant,
  scrollToBottomInstant,
  scrollToBottomSmooth,
  smoothScrollToBottom: onScrollToBottomClick,
  beginStickyFollow,
  endStickyFollow,
  completeStickyFollowSession,
  /** @deprecated 使用 beginStickyFollow */
  forceScrollToBottom: beginStickyFollow,
  isAtBottom,
  addMessage: (message: ChatMessage) => {
    displayMessages.value.push(message)
    nextTick(() => scrollToBottom())
  },
  setHasMoreHistory,
  setLoadingMore,
  getScrollProgress,
  getMessageProgress,
})
</script>

<style lang="scss" scoped>
.message-list {
  position: relative;
  flex: 1;
  overflow-y: auto;
  padding: 24px 24px 120px;
  padding-left: 88px;
  /* 自动滚动由 JS 控制 behavior，避免与 scrollTo 叠加 */

  .messages-wrapper {
    max-width: 800px;
    margin: 0 auto;
  }
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #9ca3af;
  font-size: 13px;
  opacity: 0;
  animation: fadeIn 0.3s ease forwards;

  .spinner {
    width: 16px;
    height: 16px;
    animation: spin 1s linear infinite;
    color: #6b7280;
  }
}

.no-more-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: #9ca3af;
  font-size: 12px;
  opacity: 0.8;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, transparent, #e5e7eb 50%, transparent);
    margin: 0 12px;
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: #9ca3af;
  font-size: 14px;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
