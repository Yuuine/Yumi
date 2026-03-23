<template>
  <div class="message-item" :class="message.role">
    <div class="message-bubble">
      <MarkdownRenderer v-if="message.role === 'assistant'" :content="message.content" />
      <div v-else class="message-text">{{ message.content }}</div>
    </div>
    <MessageActionsFooter :message="message" @copy-content="handleCopy" />
  </div>
</template>

<script setup lang="ts">
import type { ChatMessage } from '@/types'
import MessageActionsFooter from './MessageActionsFooter.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import { copyToClipboard } from '@/utils'
import { useToast } from '@/composables/useToast'

const toast = useToast()

interface Props {
  message: ChatMessage
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'copy-content': [content: string]
}>()

async function handleCopy(content: string): Promise<void> {
  const success = await copyToClipboard(content)
  if (success) {
    toast.success('已复制到剪贴板')
    emit('copy-content', props.message.content)
  } else {
    toast.error('复制失败，请重试')
  }
}
</script>

<style lang="scss" scoped>
.message-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;

  &.user {
    align-items: flex-end;

    .message-bubble {
      background: #f5f5f5;
      color: #333333;
      border-radius: 12px 12px 4px 12px;
    }
  }

  &.assistant {
    align-items: flex-start;

    .message-bubble {
      background: #f2f2f7;
      color: var(--text-primary);
      border-radius: 12px 12px 12px 4px;
    }
  }
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  word-break: break-word;
  line-height: 1.5;
}

.message-text {
  font-size: var(--font-size-lg);
  white-space: pre-wrap;
}
</style>
