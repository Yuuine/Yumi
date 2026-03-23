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
import { ref, watch, nextTick, onMounted, onUnmounted, computed } from 'vue'
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
let resizeScrollPending = false

const displayMessages = ref<ChatMessage[]>([])
const isLoadingMore = ref(false)
const hasMoreHistory = ref(true)
const isNearBottom = ref(true)
const isInternalUpdate = ref(false)
const isInitialLoad = ref(true)
const scrollDebounceTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const isAutoScrolling = ref(false)
const showScrollButton = ref(false)

/** 本轮发送起是否跟随到底（用户上滑会清除） */
const stickyFollowActive = ref(false)

let followScrollRafId: number | null = null
let streamThrottleTimer: ReturnType<typeof setTimeout> | null = null
let lastFollowScrollTs = 0

const SCROLL_THRESHOLD = 150
const DEBOUNCE_DELAY = 100
const BOTTOM_THRESHOLD = 50
/** 流式输出时两次平滑滚动的最小间隔（ms） */
const STREAM_SCROLL_MIN_INTERVAL_MS = 100

const isAtBottom = computed(() => {
  if (!containerRef.value) return true
  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  return scrollHeight - scrollTop - clientHeight < BOTTOM_THRESHOLD
})

function shouldAutoScroll(): boolean {
  return stickyFollowActive.value || isAtBottom.value
}

function beginStickyFollow(): void {
  stickyFollowActive.value = true
}

function endStickyFollow(): void {
  stickyFollowActive.value = false
}

/**
 * 发送/流式结束后由父组件调用：在 DOM 与滚动调度就绪后再结束粘性会话（替代在 ChatView 里手写 nextTick+rAF）。
 */
async function completeStickyFollowSession(): Promise<void> {
  await nextTick()
  await new Promise<void>(resolve => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve())
    })
  })
  endStickyFollow()
}

/**
 * Markdown/图片等导致列表高度变化时，若用户处于跟随或仍在底部附近，则补一次瞬时对齐。
 */
function maybeScrollOnContentResize(): void {
  if (!containerRef.value) return
  const el = containerRef.value
  const dist = el.scrollHeight - el.scrollTop - el.clientHeight
  const atBottom = dist < BOTTOM_THRESHOLD
  if (stickyFollowActive.value || atBottom) {
    scrollToBottomInstant()
  }
}

function scheduleResizeScroll(): void {
  if (resizeScrollPending) return
  resizeScrollPending = true
  requestAnimationFrame(() => {
    resizeScrollPending = false
    maybeScrollOnContentResize()
  })
}

function clearStickyIfUserAway(): void {
  if (!containerRef.value) return
  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  if (distanceFromBottom > BOTTOM_THRESHOLD) {
    stickyFollowActive.value = false
  }
}

/**
 * 瞬时到底（初始加载、历史锚点恢复、流式结束对齐）
 */
function scrollToBottomInstant(): void {
  if (!containerRef.value) return

  isAutoScrolling.value = true
  requestAnimationFrame(() => {
    if (!containerRef.value) return
    containerRef.value.scrollTop = containerRef.value.scrollHeight
    setTimeout(() => {
      isAutoScrolling.value = false
    }, 80)
  })
}

/**
 * 平滑到底（用户跟随、发送后展示）
 */
function scrollToBottomSmooth(): void {
  if (!containerRef.value) return

  isAutoScrolling.value = true
  const el = containerRef.value
  el.scrollTo({
    top: el.scrollHeight,
    behavior: 'smooth',
  })
  setTimeout(() => {
    isAutoScrolling.value = false
  }, 480)
}

/**
 * 调度一次跟随滚动：合并同一帧内多次更新；流式时用时间节流避免过于频繁
 */
function scheduleFollowScroll(options: { preferInstant?: boolean } = {}): void {
  if (!shouldAutoScroll()) return

  const now = performance.now()
  const streaming = chatStore.isStreaming
  if (streaming && !options.preferInstant) {
    if (now - lastFollowScrollTs < STREAM_SCROLL_MIN_INTERVAL_MS) {
      if (streamThrottleTimer) return
      streamThrottleTimer = setTimeout(
        () => {
          streamThrottleTimer = null
          runFollowScrollFrame({ preferInstant: false })
        },
        STREAM_SCROLL_MIN_INTERVAL_MS - (now - lastFollowScrollTs)
      )
      return
    }
  }

  if (followScrollRafId != null) return
  followScrollRafId = requestAnimationFrame(() => {
    followScrollRafId = null
    runFollowScrollFrame(options)
  })
}

function runFollowScrollFrame(options: { preferInstant?: boolean } = {}): void {
  if (!shouldAutoScroll() || !containerRef.value) return

  nextTick(() => {
    requestAnimationFrame(() => {
      if (!shouldAutoScroll() || !containerRef.value) return

      lastFollowScrollTs = performance.now()

      if (options.preferInstant || chatStore.isStreaming) {
        scrollToBottomInstant()
      } else {
        scrollToBottomSmooth()
      }
    })
  })
}

/** 用户点击「回到底部」：恢复跟随并平滑滚动 */
function onScrollToBottomClick(): void {
  beginStickyFollow()
  scrollToBottomSmooth()
}

watch(
  () => chatStore.isStreaming,
  (streaming, wasStreaming) => {
    if (wasStreaming && !streaming) {
      nextTick(() => {
        if (stickyFollowActive.value || isAtBottom.value) {
          scrollToBottomInstant()
        }
        emit('scrollStateChange', isAtBottom.value)
      })
    }
  }
)

/** 切换会话时重置「首屏」标记，避免与上一会话条数相同导致不走滚动逻辑（跳过首次 prev===undefined） */
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
      scheduleResizeScroll()
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
  if (streamThrottleTimer) {
    clearTimeout(streamThrottleTimer)
  }
  if (followScrollRafId != null) {
    cancelAnimationFrame(followScrollRafId)
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
        scrollToBottomInstant()
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

      if (shouldAutoScroll()) {
        nextTick(() => {
          scheduleFollowScroll({ preferInstant: false })
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

      if (isUpdatingLastMessage && shouldAutoScroll()) {
        nextTick(() => {
          scheduleFollowScroll({
            preferInstant: chatStore.isStreaming,
          })
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

  if (isAutoScrolling.value) return

  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  const currentIsAtBottom = distanceFromBottom < BOTTOM_THRESHOLD

  isNearBottom.value = distanceFromBottom < 100
  showScrollButton.value = !currentIsAtBottom

  clearStickyIfUserAway()

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
    nextTick(() => scheduleFollowScroll({ preferInstant: false }))
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
  padding: 24px 24px 200px;
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
