<template>
  <div class="chat-view">
    <SidebarNav @open-models="openModelsModal" />

    <div class="chat-main">
      <MessageList ref="messageListRef" :messages="chatStore.messages" @copy="handleCopy" />
    </div>

    <ChatInput @send="handleSend" />

    <ModelsModal :visible="showModelsModal" @close="closeModelsModal" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores'
import { SidebarNav } from '@/components/sidebar'
import { MessageList, ChatInput } from '@/components/chat'
import ModelsModal from '@/components/models/ModelsModal.vue'
import type { ChatMessage } from '@/types'

const chatStore = useChatStore()
const messageListRef = ref<InstanceType<typeof MessageList> | null>(null)
const showModelsModal = ref(false)

function handleSend(content: string) {
  const newMessage: ChatMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    content,
    timestamp: new Date().toISOString(),
  }

  messageListRef.value?.addMessage(newMessage)
}

function handleCopy(content: string) {
  window.navigator.clipboard.writeText(content)
}

function openModelsModal() {
  showModelsModal.value = true
}

function closeModelsModal() {
  showModelsModal.value = false
}
</script>

<style lang="scss" scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;
}
</style>
