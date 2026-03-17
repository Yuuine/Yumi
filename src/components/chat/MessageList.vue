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

const displayMessages = ref<ChatMessage[]>([])

onMounted(() => {
  scrollToBottom()
})

watch(
  () => props.messages,
  newMessages => {
    displayMessages.value = [...newMessages]
    nextTick(scrollToBottom)
  },
  { deep: true, immediate: true }
)

function scrollToBottom() {
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  }
}

function handleCopy(content: string) {
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
