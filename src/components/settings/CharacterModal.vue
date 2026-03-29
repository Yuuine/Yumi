<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="character-modal-overlay" @click.self="handleClose">
        <div class="character-modal">
          <div class="modal-header">
            <h2 class="modal-title">角色配置</h2>
            <div class="character-selector" v-if="allCharacters.length > 0">
              <button class="character-select-btn" @click="toggleDropdown">
                <span class="character-name">{{ currentCharacterName }}</span>
                <span class="dropdown-arrow" :class="{ open: isDropdownOpen }">▼</span>
              </button>
              <div class="dropdown-menu" v-if="isDropdownOpen">
                <div
                  v-for="char in allCharacters"
                  :key="char.id"
                  class="dropdown-item"
                  :class="{ active: char.id === currentCharacterId }"
                  @click="selectCharacter(char.id)"
                >
                  {{ char.name || '未命名角色' }}
                </div>
              </div>
            </div>
            <div class="header-actions">
              <button type="button" class="toolbar-btn secondary" @click="handleCreateNew">
                新建
              </button>
              <button
                type="button"
                class="toolbar-btn"
                :disabled="settingsRef?.isSaving"
                @click="handleSave"
              >
                {{ settingsRef?.isSaving ? '保存中…' : '保存' }}
              </button>
              <button type="button" class="toolbar-btn" @click="handleReset">重置</button>
              <button type="button" class="toolbar-btn" @click="handleExport">导出</button>
              <button
                type="button"
                class="toolbar-btn delete-btn"
                @click="handleDelete"
                :disabled="allCharacters.length <= 1"
              >
                删除
              </button>
            </div>
            <button class="close-btn" type="button" aria-label="关闭" @click="handleClose">
              <IconClose />
            </button>
          </div>
          <div class="modal-body">
            <CharacterSettings
              ref="settingsRef"
              :characterId="currentCharacterId"
              @character-loaded="onCharacterLoaded"
            />
          </div>
        </div>
      </div>
    </Transition>
    <Transition name="modal">
      <div
        v-if="showDeleteConfirm"
        class="character-modal-overlay"
        @click.self="showDeleteConfirm = false"
      >
        <div class="character-modal confirm-modal">
          <div class="modal-header">
            <h2 class="modal-title">确认删除</h2>
          </div>
          <div class="modal-body">
            <p class="confirm-message">
              删除角色后，该角色下的所有对话实例也会被一并删除。该操作不可恢复，是否继续？
            </p>
            <p v-if="deleteConversationCount > 0" class="confirm-subtext">
              当前将删除 {{ deleteConversationCount }} 个关联对话。
            </p>
          </div>
          <div class="modal-footer">
            <button type="button" class="toolbar-btn" @click="showDeleteConfirm = false">
              取消
            </button>
            <button type="button" class="toolbar-btn delete-btn" @click="confirmDelete">
              确认删除
            </button>
          </div>
        </div>
      </div>
    </Transition>
    <Transition name="modal">
      <div
        v-if="showResetConfirm"
        class="character-modal-overlay"
        @click.self="showResetConfirm = false"
      >
        <div class="character-modal confirm-modal">
          <div class="modal-header">
            <h2 class="modal-title">确认重置</h2>
          </div>
          <div class="modal-body">
            <p class="confirm-message">是否确认重置该角色卡为默认配置，此操作不可撤销。</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="toolbar-btn" @click="showResetConfirm = false">
              取消
            </button>
            <button type="button" class="toolbar-btn delete-btn" @click="confirmReset">
              确认重置
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { nextTick, ref, watch, computed } from 'vue'
import { IconClose } from '@/components/icons'
import CharacterSettings from './CharacterSettings.vue'
import { useAccountStore } from '@/stores'
import { conversationsApi } from '@/api'
import type { AccountCharacter } from '@/types/character'
import { logger } from '@/utils/logger'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const accountStore = useAccountStore()
const toast = useToast()
const settingsRef = ref<InstanceType<typeof CharacterSettings> | null>(null)
const isDropdownOpen = ref(false)
const allCharacters = ref<AccountCharacter[]>([])
const currentCharacterId = ref<string | null>(null)
const showDeleteConfirm = ref(false)
const showResetConfirm = ref(false)
const deleteConversationCount = ref(0)

const currentCharacterName = computed(() => {
  const char = allCharacters.value.find(c => c.id === currentCharacterId.value)
  return char?.name || '未命名角色'
})

async function getRelatedConversationIds(characterId: string): Promise<Set<string>> {
  if (!accountStore.currentAccount) return new Set()

  const [backendResult, localConversations] = await Promise.all([
    conversationsApi.getConversations(accountStore.currentAccount.id, characterId, 200, 0),
    accountStore.loadConversations(),
  ])

  const localMatches = localConversations.filter(
    conv => (conv.characterId || (conv as { character_id?: string }).character_id) === characterId
  )

  return new Set<string>([
    ...backendResult.conversations.map(conv => conv.id),
    ...localMatches.map(conv => conv.id),
  ])
}

function handleClose(): void {
  emit('close')
  isDropdownOpen.value = false
}

async function handleSave(): Promise<void> {
  await settingsRef.value?.save()
  await loadCharacters()
}

function handleReset(): void {
  showResetConfirm.value = true
}

async function confirmReset(): Promise<void> {
  try {
    await settingsRef.value?.resetToDefault()
    await loadCharacters()
    toast.success('已重置为系统默认配置')
  } catch (error) {
    logger.error('CharacterModal', 'Failed to reset character', error)
    toast.error('重置失败')
  } finally {
    showResetConfirm.value = false
  }
}

function handleExport(): void {
  settingsRef.value?.exportJson()
}

function handleDelete(): void {
  if (!currentCharacterId.value || !accountStore.currentAccount) {
    showDeleteConfirm.value = true
    return
  }

  const deletingCharacterId = currentCharacterId.value
  void (async () => {
    try {
      const conversationIds = await getRelatedConversationIds(deletingCharacterId)
      deleteConversationCount.value = conversationIds.size
    } catch (error) {
      logger.warn('CharacterModal', 'Failed to pre-calculate related conversations count', {
        error: error as Error,
      })
      deleteConversationCount.value = 0
    } finally {
      showDeleteConfirm.value = true
    }
  })()
}

async function confirmDelete(): Promise<void> {
  try {
    if (!currentCharacterId.value) return

    const deletingCharacterId = currentCharacterId.value
    const charName = currentCharacterName.value
    let deletedConversationCount = 0

    const conversationIds = await getRelatedConversationIds(deletingCharacterId)
    deleteConversationCount.value = conversationIds.size

    for (const conversationId of conversationIds) {
      try {
        await conversationsApi.deleteConversation(conversationId)
      } catch (error) {
        logger.warn(
          'CharacterModal',
          'Failed to delete conversation from backend, continuing local cleanup',
          { conversationId, error }
        )
      }
      await accountStore.deleteConversation(conversationId)
      deletedConversationCount += 1
    }

    await accountStore.deleteCharacter(deletingCharacterId)
    await loadCharacters()

    if (allCharacters.value.length > 0) {
      const newCharacterId = allCharacters.value[0].id
      currentCharacterId.value = newCharacterId
      await accountStore.setActiveCharacterId(newCharacterId)
      await nextTick()
      await settingsRef.value?.loadCharacter(newCharacterId)
    }

    showDeleteConfirm.value = false
    toast.success(
      deletedConversationCount > 0
        ? `已删除角色「${charName}」及 ${deletedConversationCount} 个关联对话`
        : `已删除角色「${charName}」`
    )
    logger.info('CharacterModal', 'Deleted character with related conversations', {
      characterId: deletingCharacterId,
      deletedConversationCount,
    })
  } catch (error) {
    logger.error('CharacterModal', 'Failed to delete character', error)
    toast.error('删除角色失败')
  }
}

async function handleCreateNew(): Promise<void> {
  const newChar = accountStore.createBlankCharacter()
  await accountStore.saveCharacter(newChar)
  currentCharacterId.value = newChar.id
  await accountStore.setActiveCharacterId(newChar.id)
  await loadCharacters()
  await nextTick()
  await settingsRef.value?.loadCharacter(newChar.id)
}

function toggleDropdown(): void {
  isDropdownOpen.value = !isDropdownOpen.value
}

async function selectCharacter(charId: string): Promise<void> {
  isDropdownOpen.value = false
  currentCharacterId.value = charId
  await accountStore.setActiveCharacterId(charId)
  await nextTick()
  await settingsRef.value?.loadCharacter(charId)
}

async function loadCharacters(): Promise<void> {
  allCharacters.value = await accountStore.loadCharacters()
}

function onCharacterLoaded(charId: string): void {
  currentCharacterId.value = charId
}

watch(
  () => props.visible,
  async v => {
    if (v) {
      await loadCharacters()
      await nextTick()
      await settingsRef.value?.loadCharacter()
    }
  }
)
</script>

<style lang="scss" scoped>
.character-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 16px;
  box-sizing: border-box;
}

.character-modal {
  position: relative;
  background: #ffffff;
  border-radius: 12px;
  width: min(95vw, 1200px);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;

  .modal-title {
    margin: 0;
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: #333333;
    min-width: 0;
  }

  .header-actions {
    margin-left: auto;
  }
}

.character-selector {
  position: relative;
  flex-shrink: 0;
}

.character-select-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
  }

  .character-name {
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .dropdown-arrow {
    font-size: 10px;
    transition: transform 0.2s;

    &.open {
      transform: rotate(180deg);
    }
  }
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: auto;
  min-width: 200px;
  max-height: 300px;
  overflow-y: auto;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  z-index: 2001;
}

.dropdown-item {
  padding: 10px 14px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: #f3f4f6;
  }

  &.active {
    background: #eff6ff;
    color: #1d4ed8;
    font-weight: 500;
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.toolbar-btn {
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

  &.secondary {
    background: #dbeafe;
    color: #1d4ed8;
    border-color: #93c5fd;

    &:hover:not(:disabled) {
      background: #bfdbfe;
    }
  }
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #9ca3af;
  transition: all 0.2s;
  flex-shrink: 0;

  &:hover {
    background: #f3f4f6;
    color: #333333;
  }

  svg {
    width: 20px;
    height: 20px;
  }
}

.modal-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 16px 20px 20px;
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

.toolbar-btn.delete-btn {
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

.confirm-modal {
  width: min(95vw, 450px);
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

.confirm-subtext {
  margin: 10px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.modal-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}
</style>
