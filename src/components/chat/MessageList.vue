<template>
  <div class="message-list" ref="containerRef">
    <div class="messages-wrapper">
      <MessageItem
        v-for="message in displayMessages"
        :key="message.id"
        :message="message"
        @copy="handleCopy"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import type { ChatMessage } from '@/types'
import MessageItem from './MessageItem.vue'

interface Props {
  messages?: ChatMessage[]
}

const props = withDefaults(defineProps<Props>(), {
  messages: () => [],
})

const emit = defineEmits<{
  copy: [content: string]
}>()

const containerRef = ref<HTMLElement | null>(null)

const mockMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'user',
    content: '你好，今天天气怎么样？',
    timestamp: new Date(Date.now() - 300000).toISOString(),
  },
  {
    id: '2',
    role: 'assistant',
    content: '你好！今天天气晴朗，温度适宜，非常适合外出散步。你有什么计划吗？',
    timestamp: new Date(Date.now() - 240000).toISOString(),
  },
  {
    id: '3',
    role: 'user',
    content: '我想去公园走走，你觉得怎么样？',
    timestamp: new Date(Date.now() - 180000).toISOString(),
  },
  {
    id: '4',
    role: 'assistant',
    content:
      '这是个很棒的想法！去公园散步可以让你放松心情，享受大自然的美景。记得带上水和防晒霜哦！',
    timestamp: new Date(Date.now() - 120000).toISOString(),
  },
]

const displayMessages = ref<ChatMessage[]>([...mockMessages])

onMounted(() => {
  scrollToBottom()
})

watch(
  () => props.messages,
  newMessages => {
    if (newMessages.length > 0) {
      displayMessages.value = [...mockMessages, ...newMessages]
    }
    nextTick(scrollToBottom)
  },
  { deep: true }
)

function scrollToBottom() {
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  }
}

function handleCopy(content: string) {
  // TODO: 实现消息复制逻辑
  emit('copy', content)
}

defineExpose({
  scrollToBottom,
  addMessage: (message: ChatMessage) => {
    displayMessages.value.push(message)
    nextTick(scrollToBottom)
  },
})
</script>

<style lang="scss" scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 24px 140px;
  padding-left: 88px;

  .messages-wrapper {
    max-width: 800px;
    margin: 0 auto;
  }
}
</style>
