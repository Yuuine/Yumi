<template>
  <div class="chat-view">
    <SidebarNav />

    <div class="chat-main">
      <MessageList ref="messageListRef" :messages="chatStore.messages" @copy="handleCopy" />
    </div>

    <ChatInput @send="handleSend" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores'
import { SidebarNav } from '@/components/sidebar'
import { MessageList, ChatInput } from '@/components/chat'
import type { ChatMessage } from '@/types'

const chatStore = useChatStore()
const messageListRef = ref<InstanceType<typeof MessageList> | null>(null)

function handleSend(content: string) {
  const newMessage: ChatMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    content,
    timestamp: new Date().toISOString(),
  }

  messageListRef.value?.addMessage(newMessage)

  // TODO: 连接后端发送API
  // await chatStore.sendMessage(content)
}

function handleCopy(content: string) {
  // TODO: 实现剪贴板复制逻辑
  console.log('[模拟] 复制消息内容：', content)
}
</script>

<style lang="scss" scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;
  position: relative;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
</style>
