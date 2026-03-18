<template>
  <div class="message-actions-footer">
    <button class="action-btn copy-btn" @click.stop="handleCopy" title="点击复制">
      <IconCopy class="copy-icon" :stroke-width="1.5" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { IconCopy } from '@/components/icons'
import type { ChatMessage } from '@/types'

interface Props {
  message: ChatMessage
}

const props = defineProps<Props>()

const emit = defineEmits<{
  copy: [content: string]
}>()

function handleCopy() {
  emit('copy', props.message.content)
}
</script>

<style lang="scss" scoped>
.message-actions-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  padding: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-tertiary);
  opacity: 0.6;
  transition: all 0.2s ease;

  &:hover {
    opacity: 1;
    color: var(--text-primary);
    background: var(--bg-hover);
  }

  &:active {
    transform: scale(0.9);
  }
}

.copy-icon {
  width: 16px;
  height: 16px;
}
</style>
