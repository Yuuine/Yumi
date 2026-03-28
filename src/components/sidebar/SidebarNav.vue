<template>
  <div v-if="props.isExpanded" class="sidebar-nav">
    <div class="sidebar-content">
      <div class="action-buttons">
        <button class="new-chat-btn" @click="handleNewChat">
          <IconAdd />
          <span>开启新对话</span>
        </button>
      </div>

      <div class="character-list">
        <div
          v-for="group in characterGroups"
          :key="group.characterId"
          class="character-card"
          :class="{ expanded: expandedCharacters.has(group.characterId) }"
        >
          <div class="character-header" @click="toggleCharacter(group.characterId)">
            <div class="character-avatar">
              <img
                :src="getCharacterAvatar(group.characterId)"
                :alt="group.characterName"
                class="avatar-image"
              />
            </div>
            <div class="character-info">
              <span class="character-name">{{ group.characterName }}</span>
              <span class="conversation-count">{{ group.conversations.length }} 个对话</span>
            </div>
            <div class="character-actions">
              <IconChevronDown
                class="expand-icon"
                :class="{ rotated: expandedCharacters.has(group.characterId) }"
              />
            </div>
          </div>

          <Transition name="expand">
            <div
              v-if="expandedCharacters.has(group.characterId) && group.conversations.length > 0"
              class="conversation-list"
            >
              <div
                v-for="conv in group.conversations"
                :key="conv.id"
                class="conversation-item"
                :class="{ active: currentConversationId === conv.id }"
                @click.stop="handleSelectConversation(conv.id)"
              >
                <div class="conversation-content">
                  <IconChat class="conversation-icon" />
                  <span v-if="editingConversationId !== conv.id" class="conversation-title">
                    {{ conv.title || '新对话' }}
                  </span>
                  <input
                    v-else
                    v-model="editingTitle"
                    class="conversation-title-input"
                    @blur="saveTitle(conv.id)"
                    @keyup.enter="saveTitle(conv.id)"
                    @keyup.esc="cancelEdit"
                    ref="titleInputRef"
                    v-focus
                  />
                </div>
                <div class="conversation-actions">
                  <button class="action-btn" @click.stop="startEdit(conv)" title="重命名">
                    <IconEdit />
                  </button>
                  <button class="action-btn delete" @click.stop="confirmDelete(conv)" title="删除">
                    <IconDelete />
                  </button>
                </div>
              </div>
            </div>
          </Transition>
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
        <div class="user-avatar">
          <img :src="DEFAULT_AVATAR_PATH" alt="用户头像" class="user-avatar-image" />
        </div>
        <span class="user-name">{{ userDisplayName }}</span>
        <IconMore class="user-menu-icon" />
      </button>
    </div>

    <CharacterSelectDialog
      :visible="showCharacterSelect"
      :characters="characters"
      @close="showCharacterSelect = false"
      @confirm="handleCreateConversationLocal"
      @create-character="handleCreateCharacter"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useAccountStore, useChatStore } from '@/stores'
import type { AccountCharacter } from '@/types/character'
import { getAvatarPath, DEFAULT_AVATAR_PATH } from '@/utils/avatar-manager'
import {
  IconAdd,
  IconMore,
  IconModels,
  IconCharacter,
  IconChevronDown,
  IconChat,
  IconEdit,
  IconDelete,
} from '@/components/icons'
import { CharacterSelectDialog } from '@/components/common'
import { conversationsApi } from '@/api'
import { logger } from '@/utils/logger'
import { useConfirmDialog } from '@/composables/useModal'
import { useToast } from '@/composables/useToast'

interface Conversation {
  id: string
  title: string | null
  characterId: string | null
  createdAt: string
  updatedAt: string
}

interface CharacterGroup {
  characterId: string
  characterName: string
  conversations: Conversation[]
}

const accountStore = useAccountStore()
const chatStore = useChatStore()
const confirmDialog = useConfirmDialog()
const toast = useToast()

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
  deleteConversation: [conversationId: string]
}>()

const conversations = ref<Conversation[]>([])
const characters = ref<AccountCharacter[]>([])
const expandedCharacters = ref<Set<string>>(new Set())
const editingConversationId = ref<string | null>(null)
const editingTitle = ref('')
const titleInputRef = ref<HTMLInputElement | null>(null)
const showCharacterSelect = ref(false)
const isLoadingConversations = ref(false)

const vFocus = {
  mounted: (el: HTMLInputElement) => {
    nextTick(() => {
      el.focus()
      el.select()
    })
  },
}

const userDisplayName = computed(() => accountStore.currentAccount?.displayName || '用户')

const currentConversationId = computed(() => chatStore.currentConversationId)

function hashCode(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash
  }
  return hash
}

function getCharacterAvatar(characterId: string): string {
  const char = characters.value.find((c) => c.id === characterId)
  if (char?.avatar) {
    return getAvatarPath(char.avatar)
  }
  const avatarIndex = Math.abs(hashCode(characterId)) % 5
  return getAvatarPath(`avatar${avatarIndex + 1}`)
}

function mapToConversation(conv: any): Conversation {
  return {
    id: conv.id,
    title: conv.title || null,
    characterId: conv.characterId || null,
    createdAt: conv.createdAt || '',
    updatedAt: conv.updatedAt || '',
  }
}

function sortByUpdatedAt(a: Conversation, b: Conversation): number {
  return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
}

const characterGroups = computed<CharacterGroup[]>(() => {
  const charMap = new Map(characters.value.map((c) => [c.id, c]))
  const groups = new Map<string, Conversation[]>()

  for (const char of characters.value) {
    groups.set(char.id, [])
  }

  const singleCharacterId = characters.value.length === 1 ? characters.value[0].id : null
  for (const conv of conversations.value) {
    const charId = conv.characterId || singleCharacterId || 'default'
    if (!groups.has(charId)) {
      groups.set(charId, [])
    }
    groups.get(charId)!.push(conv)
  }

  return Array.from(groups.entries())
    .map(([charId, convs]) => {
      const char = charMap.get(charId)
      const fallbackName = charId === 'default' ? '未分配角色' : '未命名角色'
      return {
        characterId: charId,
        characterName: char?.name || fallbackName,
        conversations: convs.sort(sortByUpdatedAt),
      }
    })
    .sort((a, b) => {
      if (a.conversations.length === 0 && b.conversations.length > 0) return 1
      if (a.conversations.length > 0 && b.conversations.length === 0) return -1
      return a.characterName.localeCompare(b.characterName)
    })
})

function toggleCharacter(characterId: string) {
  expandedCharacters.value.has(characterId)
    ? expandedCharacters.value.delete(characterId)
    : expandedCharacters.value.add(characterId)
}

function handleNewChat() {
  if (characters.value.length > 1) {
    showCharacterSelect.value = true
  } else if (characters.value.length === 1) {
    handleCreateConversationLocal(characters.value[0].id)
  } else {
    emit('openCharacter')
  }
}

function handleCreateCharacter() {
  emit('openCharacter')
}

async function handleCreateConversationLocal(characterId: string) {
  emit('createConversation', characterId)

  try {
    const localConvs = await accountStore.loadConversations()
    if (localConvs.length > 0) {
      const sortedLocal = [...localConvs].sort(
        (a, b) => new Date(b.updatedAt || 0).getTime() - new Date(a.updatedAt || 0).getTime()
      )
      const newConv = mapToConversation(sortedLocal[0])

      const existingIndex = conversations.value.findIndex((c) => c.id === newConv.id)
      if (existingIndex === -1) {
        conversations.value.unshift(newConv)
      } else {
        conversations.value[existingIndex] = newConv
      }

      const charId = newConv.characterId || characterId
      if (charId) {
        expandedCharacters.value.add(charId)
      }

      toast.success('对话已创建')
    }
  } catch (error) {
    logger.warn('SidebarNav', 'Failed to add new conversation locally, falling back to full load', { error })
    await loadConversations(true)
    toast.success('对话已创建')
  }
}

function handleSelectConversation(conversationId: string) {
  emit('selectConversation', conversationId)
}

function startEdit(conv: Conversation) {
  editingConversationId.value = conv.id
  editingTitle.value = conv.title || '新对话'
}

function saveTitle(conversationId: string) {
  if (editingTitle.value.trim()) {
    updateConversationTitle(conversationId, editingTitle.value.trim())
  }
  cancelEdit()
}

function cancelEdit() {
  editingConversationId.value = null
  editingTitle.value = ''
}

async function updateConversationTitle(conversationId: string, title: string) {
  try {
    await conversationsApi.updateTitle(conversationId, title)
    const conv = conversations.value.find((c) => c.id === conversationId)
    if (conv) {
      conv.title = title
      await accountStore.saveConversation(conv)
    }
    await loadConversations()
    logger.info('SidebarNav', 'Conversation title updated', { conversationId, title })
  } catch (error) {
    logger.error('SidebarNav', 'Failed to update conversation title', error)
  }
}

function confirmDelete(conv: Conversation) {
  confirmDialog.showDialog(
    '删除对话',
    `确定要删除对话 "${conv.title || '新对话'}" 吗？此操作不可恢复。`,
    'warning',
    true,
    async () => {
      try {
        await conversationsApi.deleteConversation(conv.id)
        await accountStore.deleteConversation(conv.id)
        await loadConversations()
        emit('deleteConversation', conv.id)
        logger.info('SidebarNav', 'Conversation deleted', { conversationId: conv.id })
        toast.success('对话已删除')
      } catch (error) {
        logger.error('SidebarNav', 'Failed to delete conversation', error)
      }
    }
  )
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

async function loadConversations(force = false) {
  if (isLoadingConversations.value && !force) {
    logger.debug('SidebarNav', 'Already loading conversations, skipping')
    return
  }

  try {
    isLoadingConversations.value = true

    if (!accountStore.currentAccount) {
      logger.warn('SidebarNav', 'No current account available, skipping conversation load')
      return
    }

    characters.value = await accountStore.loadCharacters()

    const result = await conversationsApi.getConversations(
      accountStore.currentAccount.id,
      undefined,
      100,
      0
    )

    const backendConversations = result.conversations.map(mapToConversation)
    const localConversations = (await accountStore.loadConversations()).map(mapToConversation)

    const merged = new Map<string, Conversation>()
    backendConversations.forEach((conv) => merged.set(conv.id, conv))
    localConversations.forEach((conv) => {
      if (!merged.has(conv.id)) {
        merged.set(conv.id, conv)
      }
    })

    conversations.value = Array.from(merged.values()).sort(sortByUpdatedAt)

    characterGroups.value.forEach((group) => {
      if (group.conversations.length > 0) {
        expandedCharacters.value.add(group.characterId)
      }
    })
  } catch (error) {
    logger.error('SidebarNav', 'Failed to load conversations', error)
  } finally {
    isLoadingConversations.value = false
  }
}

onMounted(() => {
  if (accountStore.isInitialized && accountStore.currentAccount) {
    loadConversations()
  }
})

watch(
  () => accountStore.isInitialized,
  (isInitialized) => {
    if (isInitialized && accountStore.currentAccount) {
      loadConversations()
    }
  }
)

watch(
  () => accountStore.currentAccountId,
  (newAccountId, oldAccountId) => {
    if (newAccountId && newAccountId !== oldAccountId) {
      loadConversations(true)
    }
  }
)
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

.character-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.character-card {
  background: #f9fafb;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;

  &:hover {
    background: #f3f4f6;
    border-color: #e5e7eb;
  }

  &.expanded {
    background: #ffffff;
    border-color: #e5e7eb;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }
}

.character-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(124, 58, 237, 0.05);
  }
}

.character-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(124, 58, 237, 0.3);
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.character-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.character-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-count {
  font-size: 12px;
  color: #6b7280;
}

.character-actions {
  display: flex;
  align-items: center;
}

.expand-icon {
  width: 20px;
  height: 20px;
  color: #9ca3af;
  transition: transform 0.2s;

  &.rotated {
    transform: rotate(180deg);
  }
}

.conversation-list {
  padding: 0 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conversation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: #f3f4f6;

    .conversation-actions {
      opacity: 1;
    }
  }

  &.active {
    background: #ede9fe;

    .conversation-title {
      color: #7c3aed;
      font-weight: 500;
    }

    .conversation-icon {
      color: #7c3aed;
    }
  }
}

.conversation-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.conversation-icon {
  width: 16px;
  height: 16px;
  color: #9ca3af;
  flex-shrink: 0;
}

.conversation-title {
  font-size: 13px;
  color: #4b5563;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.conversation-title-input {
  flex: 1;
  font-size: 13px;
  padding: 4px 8px;
  border: 1px solid #7c3aed;
  border-radius: 4px;
  outline: none;
  background: white;
  color: #1f2937;

  &:focus {
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2);
  }
}

.conversation-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.action-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.15s;

  &:hover {
    background: #e5e7eb;
    color: #374151;
  }

  &.delete:hover {
    background: #fee2e2;
    color: #ef4444;
  }

  svg {
    width: 14px;
    height: 14px;
  }
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  max-height: 500px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
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
    -webkit-mask:
      linear-gradient(#fff 0 0) content-box,
      linear-gradient(#fff 0 0);
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

  &.nav-btn-left,
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
  overflow: hidden;
}

.user-avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
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
