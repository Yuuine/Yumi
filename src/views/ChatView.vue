<template>
  <div class="chat-view">
    <SidebarNav
      @open-models="openModelsModal"
      @open-character="openCharacterModal"
      @open-settings="openSettingsModal"
      @open-conversations="openConversationManager"
    />

    <div class="chat-main">
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
      :disabled="chatStore.isLoading"
    />
    <ModelsModal :visible="showModelsModal" @close="closeModelsModal" />
    <CharacterModal :visible="showCharacterModal" @close="closeCharacterModal" />
    <SettingsModal :visible="showSettingsModal" @close="closeSettingsModal" />
    <ConversationManagerModal v-model="showConversationManager" @select="selectConversation" />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useChatStore, useAccountStore } from '@/stores'
import { SidebarNav } from '@/components/sidebar'
import { MessageList, ChatInput } from '@/components/chat'
import ModelsModal from '@/components/models/ModelsModal.vue'
import CharacterModal from '@/components/settings/CharacterModal.vue'
import SettingsModal from '@/components/settings/SettingsModal.vue'
import ConversationManagerModal from '@/components/chat/ConversationManagerModal.vue'
import { useToast } from '@/composables/useToast'

const chatStore = useChatStore()
const accountStore = useAccountStore()
const toast = useToast()
const messageListRef = ref<InstanceType<typeof MessageList> | null>(null)
const showModelsModal = ref(false)
const showCharacterModal = ref(false)
const showSettingsModal = ref(false)
const showConversationManager = ref(false)
const isDeepThinking = ref(false)
const hasConversations = ref(false)

async function checkConversations() {
  try {
    const convs = await accountStore.loadConversations()
    hasConversations.value = convs.length > 0
  } catch {
    hasConversations.value = false
  }
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
    showConversationManager.value = true
    return
  }
  messageListRef.value?.forceScrollToBottom()
  await chatStore.sendMessage(content, isDeepThinking.value)
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

function openConversationManager() {
  console.log('openConversationManager called, setting showConversationManager to true')
  showConversationManager.value = true
  console.log('showConversationManager.value is now:', showConversationManager.value)
}

async function selectConversation(conversationId: string) {
  try {
    await chatStore.switchConversation(conversationId)
    await checkConversations()
    nextTick(() => {
      messageListRef.value?.scrollToBottom()
    })
  } catch (error) {
    console.error('Failed to switch conversation', error)
  }
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
