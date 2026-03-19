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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { ChatMessage } from '@/types'
import MessageItem from './MessageItem.vue'
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

const SCROLL_THRESHOLD = 150
const DEBOUNCE_DELAY = 100

onMounted(() => {
  // 首次加载的滚动已在 watch 中处理
})

onUnmounted(() => {
  if (scrollDebounceTimer.value) {
    clearTimeout(scrollDebounceTimer.value)
  }
})

watch(
  () => props.messages,
  (newMessages, oldMessages) => {
    const prevLength = oldMessages?.length || 0
    const newLength = newMessages.length

    // 首次加载：只更新消息，然后滚动到底部
    if (isInitialLoad.value) {
      displayMessages.value = [...newMessages]
      isInitialLoad.value = false
      nextTick(() => {
        scrollToBottom()
      })
      return
    }

    // 内部更新（加载历史）：保持位置
    if (isInternalUpdate.value) {
      displayMessages.value = [...newMessages]
      isInternalUpdate.value = false
      return
    }

    // 新消息到达：延迟滚动确保 DOM 更新
    if (newLength > prevLength) {
      displayMessages.value = [...newMessages]
      setTimeout(() => {
        scrollToBottom()
      }, 50)
    } else {
      displayMessages.value = [...newMessages]
    }
  },
  { deep: true, immediate: true }
)

function scrollToBottom() {
  if (!containerRef.value) return
  
  requestAnimationFrame(() => {
    if (!containerRef.value) return
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  })
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

  const { scrollTop, scrollHeight, clientHeight } = containerRef.value

  isNearBottom.value = scrollHeight - scrollTop - clientHeight < 100

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
    background: linear-gradient(
      to right,
      transparent,
      #e5e7eb 50%,
      transparent
    );
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
