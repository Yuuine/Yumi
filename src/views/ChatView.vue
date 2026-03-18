<template>
  <div class="chat-view">
    <SidebarNav @open-models="openModelsModal" @open-settings="openSettingsModal" />

    <div class="chat-main">
      <MessageList
        ref="messageListRef"
        :messages="chatStore.messages"
        @copy="handleCopy"
        @load-more="handleLoadMore"
      />
    </div>

    <ChatInput @send="handleSend" :disabled="chatStore.isLoading" />

    <ModelsModal :visible="showModelsModal" @close="closeModelsModal" />
    <SettingsModal :visible="showSettingsModal" @close="closeSettingsModal" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores'
import { SidebarNav } from '@/components/sidebar'
import { MessageList, ChatInput } from '@/components/chat'
import ModelsModal from '@/components/models/ModelsModal.vue'
import SettingsModal from '@/components/settings/SettingsModal.vue'

const chatStore = useChatStore()
const messageListRef = ref<InstanceType<typeof MessageList> | null>(null)
const showModelsModal = ref(false)
const showSettingsModal = ref(false)

async function handleSend(content: string) {
  await chatStore.sendMessage(content)
}

function handleCopy(content: string) {
  window.navigator.clipboard.writeText(content)
}

async function handleLoadMore() {
  const hasMore = await chatStore.loadMoreMessages()
  if (messageListRef.value) {
    messageListRef.value.setHasMoreHistory(hasMore)
    messageListRef.value.setLoadingMore(false)
  }
}

function openModelsModal() {
  showModelsModal.value = true
}

function closeModelsModal() {
  showModelsModal.value = false
}

function openSettingsModal() {
  showSettingsModal.value = true
}

function closeSettingsModal() {
  showSettingsModal.value = false
}
</script>

<style lang="scss" scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;

  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }
}
</style>
