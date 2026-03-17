<template>
  <div class="chat-container">
    <div class="chat-header">
      <h3>与 {{ roleName }} 的对话</h3>
      <div class="header-actions">
        <el-button text @click="emit('clear')">
          <el-icon><Delete /></el-icon>
          清空对话
        </el-button>
      </div>
    </div>

    <MessageList
      ref="messageListRef"
      :messages="messages"
      :is-loading="isLoading"
      :role-name="roleName"
    />

    <ChatInput
      :model-value="inputMessage"
      :is-loading="isLoading"
      @update:model-value="inputMessage = $event"
      @send="handleSend"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import type { ChatMessage } from '@/types'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'

interface Props {
  messages: ChatMessage[]
  isLoading: boolean
  roleName: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  send: [content: string]
  clear: []
}>()

const inputMessage = ref('')
const messageListRef = ref<InstanceType<typeof MessageList> | null>(null)

function handleSend() {
  if (!inputMessage.value.trim() || props.isLoading) return
  emit('send', inputMessage.value)
  inputMessage.value = ''
}

watch(
  () => props.messages.length,
  () => {
    nextTick(() => {
      messageListRef.value?.scrollToBottom()
    })
  }
)
</script>

<style lang="scss" scoped>
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;

  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid var(--border-color, #e4e7ed);

    h3 {
      margin: 0;
      font-size: var(--font-size-md);
      font-weight: 500;
      color: var(--text-primary);
    }
  }
}
</style>
