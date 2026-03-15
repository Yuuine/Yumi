<template>
  <div class="chat-input">
    <el-input
      :model-value="modelValue"
      type="textarea"
      :rows="3"
      placeholder="输入消息..."
      @keydown.enter.exact.prevent="handleSend"
      @update:model-value="handleInput"
      :disabled="isLoading"
    />
    <div class="input-actions">
      <span class="char-count">{{ modelValue.length }} / 2000</span>
      <el-button
        type="primary"
        @click="handleSend"
        :loading="isLoading"
        :disabled="!modelValue.trim()"
      >
        <el-icon><Promotion /></el-icon>
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Promotion } from '@element-plus/icons-vue'

interface Props {
  modelValue: string
  isLoading: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
}>()

function handleInput(value: string) {
  emit('update:modelValue', value)
}

function handleSend() {
  emit('send')
}
</script>

<style lang="scss" scoped>
.chat-input {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #e4e7ed);
  background: var(--bg-primary);

  .messages-wrapper {
    max-width: 800px;
    margin: 0 auto;
  }

  .input-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;

    .char-count {
      font-size: 12px;
      color: var(--text-secondary);
    }
  }
}
</style>
