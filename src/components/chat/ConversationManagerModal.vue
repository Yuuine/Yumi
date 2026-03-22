<template>
  <Dialog
    v-model="localVisible"
    title="对话管理"
    size="large"
    @confirm="handleConfirm"
    @cancel="handleCancel"
    @close="handleClose"
    :showIcon="false"
    :showCancel="false"
    :showClose="true"
  >
    <CharacterSelectorModal
      v-model="showCharacterSelector"
      @confirm="handleCharacterSelected"
    />
    <div class="conversation-manager">
      <div class="conversation-list">
        <div v-if="conversations.length === 0" class="empty-state">
          <p>暂无对话</p>
        </div>
        <div
          v-else
          v-for="conversation in conversations"
          :key="conversation.id"
          class="conversation-item"
          :class="{ active: conversation.id === activeConversationId }"
          @click="selectConversation(conversation.id)"
        >
          <div class="conversation-info">
            <div class="conversation-title">{{ conversation.title || '新对话' }}</div>
            <div class="conversation-meta">
              <span class="character-name">{{ getCharacterName(conversation.characterId) }}</span>
              <span class="conversation-date">{{ formatDate(conversation.updatedAt) }}</span>
            </div>
          </div>
          <div class="conversation-actions">
            <button class="action-btn delete-btn" @click.stop="deleteConversation(conversation.id)">
              <IconDelete class="btn-icon" />
            </button>
          </div>
        </div>
      </div>
      <div class="conversation-footer">
        <button class="new-conversation-btn" @click="createNewConversation">
          <IconAdd class="btn-icon" />
          <span>新建对话</span>
        </button>
      </div>
    </div>
  </Dialog>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="showDeleteConfirm" class="character-modal-overlay" @click.self="showDeleteConfirm = false">
        <div class="character-modal confirm-modal">
          <div class="modal-header">
            <h2 class="modal-title">确认删除</h2>
          </div>
          <div class="modal-body">
            <p class="confirm-message">此操作不可逆，将永久删除此对话的所有历史记录。</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="toolbar-btn" @click="showDeleteConfirm = false">取消</button>
            <button type="button" class="toolbar-btn delete-btn" @click="confirmDelete">确认删除</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAccountStore, useChatStore } from '@/stores'
import Dialog from '@/components/common/Dialog.vue'
import CharacterSelectorModal from './CharacterSelectorModal.vue'
import { IconAdd, IconDelete } from '@/components/icons'
import { logger } from '@/utils/logger'
import { useToast } from '@/composables/useToast'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', conversationId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const accountStore = useAccountStore()
const chatStore = useChatStore()
const toast = useToast()

const localVisible = ref(props.modelValue)
const showCharacterSelector = ref(false)
const showDeleteConfirm = ref(false)
const deletingConversationId = ref<string | null>(null)

const activeConversationId = computed(() => chatStore.currentConversationId)
const conversations = ref<
  Array<{ id: string; title?: string; characterId?: string; updatedAt?: string }>
>([])
const charactersById = ref<Record<string, { name?: string }>>({})

async function loadConversations() {
  try {
    const loaded = await accountStore.loadConversations()
    conversations.value = loaded as Array<{
      id: string
      title?: string
      characterId?: string
      updatedAt?: string
    }>

    const chars = await accountStore.loadCharacters()
    charactersById.value = {}
    for (const char of chars) {
      charactersById.value[char.id] = char
    }
  } catch (error) {
    logger.error('ConversationManager', 'Failed to load conversations', error)
  }
}

watch(
  () => props.modelValue,
  async (newVal) => {
    console.log('ConversationManagerModal: modelValue prop changed to:', newVal)
    localVisible.value = newVal
    if (newVal) {
      await loadConversations()
    }
  },
  { immediate: true }
)

watch(localVisible, (newVal) => {
  emit('update:modelValue', newVal)
})

function handleConfirm() {
  emit('update:modelValue', false)
}

function handleCancel() {
  emit('update:modelValue', false)
}

function handleClose() {
  emit('update:modelValue', false)
}

function getCharacterName(characterId?: string): string {
  if (!characterId) return '未选择角色'
  const char = charactersById.value[characterId]
  return char?.name || '未知角色'
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return date.toLocaleDateString('zh-CN')
}

async function selectConversation(conversationId: string) {
  try {
    emit('select', conversationId)
    emit('update:modelValue', false)
  } catch (error) {
    logger.error('ConversationManager', 'Failed to select conversation', error)
  }
}

async function createNewConversation() {
  try {
    const characters = await accountStore.loadCharacters()
    
    if (characters.length === 0) {
      return
    }
    
    const hasExistingConversations = conversations.value.length > 0
    
    if (hasExistingConversations || characters.length > 1) {
      showCharacterSelector.value = true
    } else {
      await chatStore.startNewConversation(characters[0].id)
      await loadConversations()
      toast.success('已创建新对话')
      emit('update:modelValue', false)
    }
  } catch (error) {
    logger.error('ConversationManager', 'Failed to create new conversation', error)
    toast.error('创建对话失败')
  }
}

async function handleCharacterSelected(characterId: string) {
  try {
    await chatStore.startNewConversation(characterId)
    await loadConversations()
    toast.success('已创建新对话')
    emit('update:modelValue', false)
  } catch (error) {
    logger.error('ConversationManager', 'Failed to create conversation with character', error)
    toast.error('创建对话失败')
  }
}

async function deleteConversation(conversationId: string) {
  try {
    if (conversationId === activeConversationId.value) {
      toast.warning('当前正在使用的对话无法删除')
      return
    }
    
    deletingConversationId.value = conversationId
    showDeleteConfirm.value = true
  } catch (error) {
    logger.error('ConversationManager', 'Failed to show delete confirm', error)
  }
}

async function confirmDelete() {
  try {
    if (!deletingConversationId.value) return
    
    await accountStore.deleteConversation(deletingConversationId.value)
    await loadConversations()
    toast.success('已删除对话')
    showDeleteConfirm.value = false
    deletingConversationId.value = null
  } catch (error) {
    logger.error('ConversationManager', 'Failed to delete conversation', error)
    toast.error('删除对话失败')
  }
}
</script>

<style lang="scss" scoped>
.conversation-manager {
  display: flex;
  flex-direction: column;
  max-height: 60vh;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: var(--bg-hover);
    border-color: var(--border-color);
  }

  &.active {
    border-color: var(--color-primary);
    background: var(--color-primary-light-9);
  }
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-meta {
  display: flex;
  gap: 12px;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.conversation-actions {
  margin-left: 12px;
}

.action-btn {
  padding: 8px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-secondary);

  &:hover {
    background: var(--bg-hover);
  }

  &.delete-btn:hover {
    color: var(--color-danger);
    background: var(--color-danger-light-9);
  }
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.conversation-footer {
  padding-top: 16px;
  border-top: 1px solid var(--border-color-lighter);
}

.new-conversation-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-md);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  font-weight: 500;

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
    background: var(--color-primary-light-9);
  }
}

.character-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 4000;
  padding: 20px;
}

.character-modal {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  min-width: min(90vw, 600px);
  max-width: 900px;
}

.confirm-modal {
  width: min(95vw, 450px);
  min-width: auto;
}

.confirm-modal .modal-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;

  .modal-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #333333;
    min-width: 0;
  }
}

.confirm-modal .modal-body {
  padding: 24px 20px;
  text-align: center;
}

.confirm-message {
  margin: 0;
  font-size: 15px;
  color: #374151;
  line-height: 1.6;
}

.confirm-modal .modal-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}

.confirm-modal .toolbar-btn {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition:
    background 0.15s,
    border-color 0.15s;

  &:hover:not(:disabled) {
    background: #e5e7eb;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.confirm-modal .toolbar-btn.delete-btn {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fecaca;

  &:hover:not(:disabled) {
    background: #fee2e2;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;

  .character-modal {
    transition:
      transform 0.25s ease,
      opacity 0.25s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .character-modal {
    transform: scale(0.97) translateY(-12px);
    opacity: 0;
  }
}
</style>
