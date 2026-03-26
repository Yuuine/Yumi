<template>
  <div v-if="props.isExpanded" class="sidebar-nav">
    <div class="sidebar-content">
      <div class="action-buttons">
        <button class="new-chat-btn" @click="handleNewChat">
          <IconAdd />
          <span>开启新对话</span>
        </button>
      </div>

      <div class="conversation-list">
        <div
          v-for="group in groupedConversations"
          :key="group.characterId || 'default'"
          class="time-group"
        >
          <div class="time-label">{{ getTimeLabel(group) }}</div>
          <div class="conversation-items">
            <div
              v-for="conv in group.conversations"
              :key="conv.id"
              class="conversation-item"
              :class="{ active: currentConversationId === conv.id }"
              @click="handleSelectConversation(conv.id)"
            >
              <span class="conversation-title">{{ conv.title || '新对话' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="nav-buttons-bottom">
        <button class="nav-btn-bottom nav-btn-left" @click="handleOpenModels">
          <IconModels />
          <span>模型</span>
        </button>
        <button class="nav-btn-bottom nav-btn-right" @click="handleOpenCharacter">
          <IconCharacter />
          <span>角色</span>
        </button>
      </div>
      <button class="user-item" @click="handleUserClick">
        <div class="user-avatar">{{ userAvatar }}</div>
        <span class="user-name">{{ userDisplayName }}</span>
        <IconMore class="user-menu-icon" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAccountStore, useChatStore } from '@/stores'
import { IconAdd, IconMore, IconModels, IconCharacter } from '@/components/icons'
import { conversationsApi } from '@/api'
import { logger } from '@/utils/logger'

interface Conversation {
  id: string
  title: string | null
  character_id: string | null
  created_at: string
  updated_at: string
}

interface ConversationGroup {
  characterId: string | null
  characterName: string | null
  conversations: Conversation[]
}

const accountStore = useAccountStore()
const chatStore = useChatStore()

interface Props {
  isExpanded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isExpanded: true,
})

const emit = defineEmits<{
  openSettings: []
  openCharacter: []
  openModels: []
  createConversation: [characterId: string | null]
  selectConversation: [conversationId: string]
  newChat: []
}>()

const conversations = ref<Conversation[]>([])

const userDisplayName = computed(() => {
  return accountStore.currentAccount?.displayName || '用户'
})

const userAvatar = computed(() => {
  const name = userDisplayName.value
  return name.charAt(0).toUpperCase()
})

const currentConversationId = computed(() => chatStore.currentConversationId)

const groupedConversations = computed<ConversationGroup[]>(() => {
  const groups = new Map<string, Conversation[]>()
  const now = new Date()
  
  for (const conv of conversations.value) {
    const updated = new Date(conv.updated_at)
    const diffDays = Math.floor((now.getTime() - updated.getTime()) / (1000 * 60 * 60 * 24))
    
    let key: string
    if (diffDays === 0) {
      key = 'today'
    } else if (diffDays < 7) {
      key = '7days'
    } else if (diffDays < 30) {
      key = '30days'
    } else {
      key = updated.getFullYear().toString()
    }
    
    if (!groups.has(key)) {
      groups.set(key, [])
    }
    groups.get(key)!.push(conv)
  }

  return [
    { characterId: 'today', characterName: null, conversations: groups.get('today') || [] },
    { characterId: '7days', characterName: null, conversations: groups.get('7days') || [] },
    { characterId: '30days', characterName: null, conversations: groups.get('30days') || [] },
    ...Array.from(groups.entries())
      .filter(([key]) => !['today', '7days', '30days'].includes(key))
      .map(([key, convs]) => ({
        characterId: key,
        characterName: key,
        conversations: convs.sort(
          (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        ),
      })),
  ].filter(g => g.conversations.length > 0)
})

function getTimeLabel(group: ConversationGroup): string {
  const labels: Record<string, string> = {
    'today': '昨天',
    '7days': '7天内',
    '30days': '30天内'
  }
  return labels[group.characterId || ''] || group.characterName || ''
}

function handleNewChat() {
  emit('newChat')
}

function handleSelectConversation(conversationId: string) {
  emit('selectConversation', conversationId)
}

function handleOpenModels() {
  emit('openModels')
}

function handleOpenCharacter() {
  emit('openCharacter')
}

function handleUserClick() {
  emit('openSettings')
}

async function loadConversations() {
  try {
    const result = await conversationsApi.getConversations(
      accountStore.currentAccount!.id,
      undefined,
      100,
      0
    )
    conversations.value = result.conversations.map(conv => ({
      id: conv.id,
      title: conv.title || null,
      character_id: conv.characterId || null,
      created_at: conv.createdAt || '',
      updated_at: conv.updatedAt || '',
    }))
  } catch (error) {
    logger.error('SidebarNav', 'Failed to load conversations', error)
  }
}

onMounted(() => {
  loadConversations()
})
</script>

<style lang="scss" scoped>
.sidebar-nav {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  width: 280px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
}

.action-buttons {
  padding: 8px 0 16px;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  &:hover {
    background: #f9fafb;
    border-color: #d1d5db;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  }

  &:active {
    transform: scale(0.98);
  }

  svg {
    width: 20px;
    height: 20px;
  }
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 4px;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
  }
}

.time-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.time-label {
  font-size: 13px;
  font-weight: 600;
  color: #9ca3af;
  padding: 4px 8px;
  letter-spacing: 0.2px;
}

.conversation-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.conversation-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: #f3f4f6;
  }

  &.active {
    background: #f3f4f6;
  }
}

.conversation-title {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.nav-buttons-bottom {
  display: flex;
  flex-direction: row;
  gap: 12px;
  width: 100%;
}

.nav-btn-bottom {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px 12px;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.9) 0%,
      rgba(255, 255, 255, 0.7) 50%,
      rgba(255, 255, 255, 0.85) 100%
    );
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    z-index: 0;
  }

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 16px;
    padding: 1px;
    background: linear-gradient(
      135deg,
      rgba(148, 163, 184, 0.3) 0%,
      rgba(148, 163, 184, 0.1) 50%,
      rgba(148, 163, 184, 0.25) 100%
    );
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    z-index: 0;
  }

  svg,
  span {
    position: relative;
    z-index: 1;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(148, 163, 184, 0.25);

    &::before {
      background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.95) 0%,
        rgba(255, 255, 255, 0.8) 50%,
        rgba(255, 255, 255, 0.9) 100%
      );
    }
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 4px 12px rgba(148, 163, 184, 0.2);
  }

  svg {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
  }

  &.nav-btn-left {
    color: #6366f1;

    svg {
      color: #6366f1;
    }
  }

  &.nav-btn-right {
    color: #6366f1;

    svg {
      color: #6366f1;
    }
  }
}

.user-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: transparent;
  border-radius: 10px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;

  &:hover {
    background: #f3f4f6;
  }
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.user-name {
  flex: 1;
  font-size: 14px;
  color: #374151;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-menu-icon {
  width: 20px;
  height: 20px;
  color: #9ca3af;
  flex-shrink: 0;
}
</style>
