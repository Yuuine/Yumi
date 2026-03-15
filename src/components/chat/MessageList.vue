<template>
  <div class="message-list" ref="containerRef">
    <div class="messages-wrapper">
      <template v-if="messages.length === 0">
        <EmptyState :role-name="roleName" />
      </template>

      <template v-else>
        <ChatMessageComponent v-for="message in messages" :key="message.id" :message="message" />
      </template>

      <TypingIndicator v-if="isLoading" :role-name="roleName" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import type { ChatMessage } from '@/types'
import ChatMessageComponent from '@/components/ChatMessage.vue'
import EmptyState from './EmptyState.vue'
import TypingIndicator from './TypingIndicator.vue'

interface Props {
  messages: ChatMessage[]
  isLoading: boolean
  roleName: string
}

const props = defineProps<Props>()

const containerRef = ref<HTMLElement | null>(null)

function scrollToBottom() {
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  }
}

watch(
  () => props.messages.length,
  () => {
    nextTick(scrollToBottom)
  }
)

defineExpose({
  scrollToBottom,
})
</script>

<style lang="scss" scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px;

  .messages-wrapper {
    max-width: 800px;
    margin: 0 auto;
  }
}
</style>
