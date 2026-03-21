<template>
  <div class="message-list" ref="containerRef" @scroll="handleScroll">
    <div class="messages-wrapper" ref="wrapperRef">
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
        @copy="handleCopy"
      />

      <div v-if="displayMessages.length === 0 && !isLoadingMore" class="empty-state">
        <span>暂无消息</span>
      </div>
    </div>

    <ScrollToBottom :visible="showScrollButton" @click="smoothScrollToBottom" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted, computed } from 'vue'
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
  copy: [content: string]
  loadMore: []
  scrollStateChange: [isAtBottom: boolean]
}>()

const containerRef = ref<HTMLElement | null>(null)
const wrapperRef = ref<HTMLElement | null>(null)

const displayMessages = ref<ChatMessage[]>([])
const isLoadingMore = ref(false)
const hasMoreHistory = ref(true)
const isNearBottom = ref(true)
const isInternalUpdate = ref(false)
const isInitialLoad = ref(true)
const scrollDebounceTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const isAutoScrolling = ref(false)
const showScrollButton = ref(false)

const SCROLL_THRESHOLD = 150
const DEBOUNCE_DELAY = 100
const BOTTOM_THRESHOLD = 50

const isAtBottom = computed(() => {
  if (!containerRef.value) return true
  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  return scrollHeight - scrollTop - clientHeight < BOTTOM_THRESHOLD
})

onMounted(() => {
  // 首次加载的滚动已在 watch 中处理
})

onUnmounted(() => {
  if (scrollDebounceTimer.value) {
    clearTimeout(scrollDebounceTimer.value)
  }
})

const forceScrollFlag = ref(false)

watch(
  () => props.messages,
  (newMessages, oldMessages) => {
    const prevLength = oldMessages?.length || 0
    const newLength = newMessages.length

    // 首次加载：直接显示消息并滚动到底部
    if (isInitialLoad.value) {
      displayMessages.value = [...newMessages]
      isInitialLoad.value = false
      nextTick(() => {
        scrollToBottom()
        emit('scrollStateChange', true)
      })
      return
    }

    // 内部更新（加载历史消息）：保持当前滚动位置
    if (isInternalUpdate.value) {
      displayMessages.value = [...newMessages]
      isInternalUpdate.value = false
      return
    }

    // 接收新消息：根据用户位置或强制滚动标志决定是否自动滚动
    if (newLength > prevLength) {
      displayMessages.value = [...newMessages]

      // 强制滚动（用户发送消息时）
      if (forceScrollFlag.value) {
        forceScrollFlag.value = false
        nextTick(() => {
          scrollToBottom()
          emit('scrollStateChange', true)
        })
        return
      }

      // 用户在底部位置，自动滚动到底部查看新消息
      const wasAtBottom = isAtBottom.value
      if (wasAtBottom) {
        nextTick(() => {
          scrollToBottom()
          emit('scrollStateChange', true)
        })
      }
      // 用户不在底部时，不自动滚动，保持当前位置
      // 滚动按钮由 handleScroll 中的 scrollStateChange 事件控制
    } else {
      displayMessages.value = [...newMessages]
    }
  },
  { deep: true, immediate: true }
)

function scrollToBottom() {
  if (!containerRef.value) return

  isAutoScrolling.value = true
  requestAnimationFrame(() => {
    if (!containerRef.value) return
    containerRef.value.scrollTop = containerRef.value.scrollHeight
    setTimeout(() => {
      isAutoScrolling.value = false
    }, 100)
  })
}

function smoothScrollToBottom() {
  if (!containerRef.value) return

  isAutoScrolling.value = true
  containerRef.value.scrollTo({
    top: containerRef.value.scrollHeight,
    behavior: 'smooth',
  })
  setTimeout(() => {
    isAutoScrolling.value = false
  }, 500)
}

function forceScrollToBottom() {
  forceScrollFlag.value = true
}

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
    messageEl.scrollIntoView({ block: 'start' })
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

  // 获取当前可见的第一个消息ID
  const firstVisibleId = getFirstVisibleMessageId()

  isInternalUpdate.value = true
  emit('loadMore')

  await waitForDomUpdate()

  nextTick(() => {
    // 滚动到之前可见的消息位置
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
  emit('copy', content)
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
  scrollToBottom,
  smoothScrollToBottom,
  forceScrollToBottom,
  isAtBottom,
  addMessage: (message: ChatMessage) => {
    displayMessages.value.push(message)
    nextTick(scrollToBottom)
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
  scroll-behavior: smooth;

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
