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
        @copy="handleCopy"
      />

      <div v-if="displayMessages.length === 0 && !isLoadingMore" class="empty-state">
        <span>暂无消息</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
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

const SCROLL_THRESHOLD = 150

onMounted(() => {
  scrollToBottom()
})

watch(
  () => props.messages,
  newMessages => {
    if (newMessages.length > displayMessages.value.length) {
      const prevHeight = containerRef.value?.scrollHeight || 0
      displayMessages.value = [...newMessages]
      nextTick(() => {
        if (isNearBottom.value) {
          scrollToBottom()
        } else {
          maintainScrollPosition(prevHeight)
        }
      })
    } else {
      displayMessages.value = [...newMessages]
    }
  },
  { deep: true, immediate: true }
)

function scrollToBottom() {
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  }
}

function maintainScrollPosition(prevHeight: number) {
  if (containerRef.value) {
    const newHeight = containerRef.value.scrollHeight
    containerRef.value.scrollTop = newHeight - prevHeight
  }
}

function handleScroll() {
  if (!containerRef.value) return

  const { scrollTop, scrollHeight, clientHeight } = containerRef.value

  isNearBottom.value = scrollHeight - scrollTop - clientHeight < 100

  if (scrollTop < SCROLL_THRESHOLD && !isLoadingMore.value && hasMoreHistory.value) {
    loadMoreHistory()
  }
}

async function loadMoreHistory() {
  if (isLoadingMore.value || !hasMoreHistory.value) return

  isLoadingMore.value = true

  const prevHeight = containerRef.value?.scrollHeight || 0

  emit('loadMore')

  await new Promise(resolve => setTimeout(resolve, 300))

  nextTick(() => {
    maintainScrollPosition(prevHeight)
    isLoadingMore.value = false
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

defineExpose({
  scrollToBottom,
  addMessage: (message: ChatMessage) => {
    displayMessages.value.push(message)
    nextTick(scrollToBottom)
  },
  setHasMoreHistory,
  setLoadingMore,
})
</script>

<style lang="scss" scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 24px 200px;
  padding-left: 88px;
  scroll-behavior: smooth;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;

    &:hover {
      background: #9ca3af;
    }
  }

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

  .spinner {
    width: 16px;
    height: 16px;
    animation: spin 1s linear infinite;
  }
}

.no-more-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: #d1d5db;
  font-size: 12px;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #e5e7eb;
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
</style>
