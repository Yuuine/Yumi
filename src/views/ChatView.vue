<template>
  <div class="chat-view">
    <SideMenu
      :role-name="userStore.profile.roleName"
      :conversation-count="chatStore.conversationCount"
      :memory-count="memoryStats?.totalMemories || 0"
      :active-menu="activeMenu"
    />

    <ChatContainer
      :messages="chatStore.messages"
      :is-loading="chatStore.isLoading"
      :role-name="userStore.profile.roleName"
      @send="handleSend"
      @clear="clearChat"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useChatStore, useUserStore, useSettingsStore } from '@/stores'
import { memoryApi } from '@/api'
import type { MemoryStats } from '@/types'
import { SideMenu } from '@/components/sidebar'
import { ChatContainer } from '@/components/chat'

const route = useRoute()
const chatStore = useChatStore()
const userStore = useUserStore()
const settingsStore = useSettingsStore()

const memoryStats = ref<MemoryStats | null>(null)

const activeMenu = ref(route.path)

watch(
  () => route.path,
  path => {
    activeMenu.value = path
  }
)

onMounted(async () => {
  await Promise.all([userStore.loadProfile(), settingsStore.loadSettings(), loadMemoryStats()])
})

async function loadMemoryStats() {
  try {
    memoryStats.value = await memoryApi.getStats(chatStore.currentUserId)
  } catch (error) {
    console.error('Failed to load memory stats:', error)
  }
}

async function handleSend(content: string) {
  await chatStore.sendMessage(content)
  await loadMemoryStats()
}

async function clearChat() {
  try {
    await ElMessageBox.confirm('确定要清空所有对话记录吗？', '确认清空', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    chatStore.clearMessages()
  } catch {
    // User cancelled
  }
}
</script>

<style lang="scss" scoped>
.chat-view {
  display: flex;
  height: 100vh;
  background: var(--bg-primary);
}
</style>
