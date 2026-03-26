<template>
  <div class="chat-view">
    <SidebarNav
      :is-expanded="sidebarExpanded"
      @open-models="openModelsModal"
      @open-character="openCharacterModal"
      @open-settings="openSettingsModal"
      @create-conversation="handleCreateConversation"
      @select-conversation="selectConversation"
      @new-chat="handleNewChat"
    />

    <div :class="['toggle-button', { 'sidebar-open': sidebarExpanded }]" @click="toggleSidebar">
      <IconSidebar />
    </div>

    <div class="chat-main" :class="{ 'sidebar-collapsed': !sidebarExpanded }">
      <MessageList
        ref="messageListRef"
        :messages="chatStore.messages"
        @copy-content="handleCopy"
        @load-more="handleLoadMore"
      />
    </div>

    <ChatInput
      v-model:deepThinking="isDeepThinking"
      @send="handleSend"
      :disabled="chatStore.isLoading || chatStore.isStreaming"
      :sidebar-collapsed="!sidebarExpanded"
    />
    <ModelsModal :visible="showModelsModal" @close="closeModelsModal" />
    <CharacterModal :visible="showCharacterModal" @close="closeCharacterModal" />
    <SettingsModal :visible="showSettingsModal" @close="closeSettingsModal" />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useChatStore, useAccountStore } from '@/stores'
import { SidebarNav } from '@/components/sidebar'
import { MessageList, ChatInput } from '@/components/chat'
import { IconSidebar } from '@/components/icons'
import ModelsModal from '@/components/models/ModelsModal.vue'
import CharacterModal from '@/components/settings/CharacterModal.vue'
import SettingsModal from '@/components/settings/SettingsModal.vue'
import { useToast } from '@/composables/useToast'
import { logger } from '@/utils/logger'

const chatStore = useChatStore()
const accountStore = useAccountStore()
const toast = useToast()
const messageListRef = ref<InstanceType<typeof MessageList> | null>(null)
const showModelsModal = ref(false)
const showCharacterModal = ref(false)
const showSettingsModal = ref(false)
const isDeepThinking = ref(false)
const hasConversations = ref(false)
const sidebarExpanded = ref(true)

/** 设为 true 时使用 SSE 流式接口（与 MessageList 粘性滚动/节流配合） */
const useChatStream = import.meta.env.VITE_CHAT_USE_STREAM === 'true'

async function checkConversations() {
  try {
    const convs = await accountStore.loadConversations()
    hasConversations.value = convs.length > 0
  } catch {
    hasConversations.value = false
  }
}

function toggleSidebar() {
  sidebarExpanded.value = !sidebarExpanded.value
}

onMounted(async () => {
  await checkConversations()
  nextTick(() => {
    messageListRef.value?.scrollToBottom()
  })
})

async function handleSend(content: string) {
  await checkConversations()
  if (!hasConversations.value && !chatStore.currentConversationId) {
    toast.warning('请先创建一个对话')
    return
  }

  messageListRef.value?.beginStickyFollow()
  try {
    if (useChatStream) {
      await chatStore.sendMessageStream(content)
    } else {
      await chatStore.sendMessage(content, isDeepThinking.value)
    }
  } finally {
    await messageListRef.value?.completeStickyFollowSession()
  }

  await checkConversations()
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

function openCharacterModal() {
  showCharacterModal.value = true
}

function closeCharacterModal() {
  showCharacterModal.value = false
}

function openSettingsModal() {
  showSettingsModal.value = true
}

function closeSettingsModal() {
  showSettingsModal.value = false
}

async function handleNewChat() {
  try {
    await chatStore.startNewConversation()
    await checkConversations()
    nextTick(() => {
      messageListRef.value?.scrollToBottom()
    })
  } catch (error) {
    logger.error('ChatView', 'Failed to create new chat', error)
  }
}

async function handleCreateConversation(characterId: string | null) {
  try {
    await chatStore.startNewConversation(characterId || undefined)
    await checkConversations()
    nextTick(() => {
      messageListRef.value?.scrollToBottom()
    })
  } catch (error) {
    logger.error('ChatView', 'Failed to create conversation', error)
  }
}

async function selectConversation(conversationId: string) {
  try {
    await chatStore.switchConversation(conversationId)
    await checkConversations()
    nextTick(() => {
      messageListRef.value?.scrollToBottom()
    })
  } catch (error) {
    logger.error('ChatView', 'Failed to switch conversation', error)
  }
}
</script>

<style lang="scss" scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;

  .toggle-button {
    position: fixed;
    top: 28px;
    left: 16px;
    z-index: 200;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    cursor: pointer;
    color: #374151;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

    &.sidebar-open {
      left: 296px;
    }

    &:hover {
      background: #f9fafb;
      border-color: #d1d5db;
    }

    svg {
      width: 20px;
      height: 20px;
    }
  }

  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
    margin-left: 280px;
    transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &.sidebar-collapsed {
      margin-left: 0;
    }
  }
}
</style>
