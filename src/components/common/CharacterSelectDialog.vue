<template>
  <ModalWrapper :visible="visible" @close="handleClose">
    <div class="character-select-dialog">
      <div v-if="characters.length === 0" class="empty-state">
        <IconCharacter class="empty-icon" />
        <p class="empty-text">暂无角色卡</p>
        <button class="create-btn" @click="handleCreateCharacter">创建角色</button>
      </div>
      <div v-else class="character-grid">
        <div
          v-for="char in sortedCharacters"
          :key="char.id"
          class="character-card-item"
          :class="{ selected: selectedCharacterId === char.id }"
          @click="selectCharacter(char.id)"
        >
          <div class="card-avatar">
            {{ char.name.charAt(0).toUpperCase() }}
          </div>
          <div class="card-info">
            <span class="card-name">{{ char.name }}</span>
            <span class="card-nickname">{{ char.nickname }}</span>
            <span v-if="char.roleOverview" class="card-desc">
              {{ char.roleOverview.slice(0, 60) }}{{ char.roleOverview.length > 60 ? '...' : '' }}
            </span>
          </div>
          <div v-if="selectedCharacterId === char.id" class="selected-indicator">
            <IconCheck />
          </div>
        </div>
      </div>
      <div v-if="characters.length > 0" class="dialog-footer">
        <button class="dialog-btn secondary" @click="handleClose">取消</button>
        <button class="dialog-btn primary" :disabled="!selectedCharacterId" @click="handleConfirm">
          开启对话
        </button>
      </div>
    </div>
  </ModalWrapper>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ModalWrapper } from '@/components/common'
import { IconCharacter, IconCheck } from '@/components/icons'
import type { AccountCharacter } from '@/types/character'

interface Props {
  visible: boolean
  characters: AccountCharacter[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  confirm: [characterId: string]
  createCharacter: []
}>()

const selectedCharacterId = ref<string>('')

const sortedCharacters = computed(() => {
  return [...props.characters].sort((a, b) => {
    const aHasOverview = a.roleOverview && a.roleOverview.trim().length > 0
    const bHasOverview = b.roleOverview && b.roleOverview.trim().length > 0

    if (aHasOverview && !bHasOverview) return -1
    if (!aHasOverview && bHasOverview) return 1

    const aUpdated = new Date(a.updatedAt).getTime()
    const bUpdated = new Date(b.updatedAt).getTime()
    if (aUpdated !== bUpdated) {
      return bUpdated - aUpdated
    }

    const aCreated = new Date(a.createdAt).getTime()
    const bCreated = new Date(b.createdAt).getTime()
    if (aCreated !== bCreated) {
      return bCreated - aCreated
    }

    return a.name.localeCompare(b.name)
  })
})

watch(
  () => props.visible,
  newVisible => {
    if (newVisible) {
      selectedCharacterId.value = ''
      if (sortedCharacters.value.length > 0) {
        selectedCharacterId.value = sortedCharacters.value[0].id
      }
    }
  }
)

function selectCharacter(characterId: string) {
  selectedCharacterId.value = characterId
}

function handleClose() {
  emit('close')
}

function handleConfirm() {
  if (selectedCharacterId.value) {
    emit('confirm', selectedCharacterId.value)
    emit('close')
  }
}

function handleCreateCharacter() {
  emit('createCharacter')
  emit('close')
}
</script>

<style lang="scss" scoped>
.character-select-dialog {
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 48px 24px;
  text-align: center;

  .empty-icon {
    width: 64px;
    height: 64px;
    color: #d1d5db;
  }

  .empty-text {
    margin: 0;
    font-size: 15px;
    color: #6b7280;
  }
}

.create-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
  }

  &:active {
    transform: translateY(0);
  }
}

.character-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  padding: 4px 0;
  flex: 1;
  overflow-y: auto;

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

.character-card-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px;
  background: #f9fafb;
  border: 2px solid transparent;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: #f3f4f6;
    border-color: #e5e7eb;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  }

  &.selected {
    background: #ede9fe;
    border-color: #7c3aed;
    box-shadow: 0 4px 16px rgba(124, 58, 237, 0.15);
  }
}

.card-avatar {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.card-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-name {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-nickname {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

.card-desc {
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-top: 4px;
}

.selected-indicator {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #7c3aed;
  border-radius: 50%;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.4);

  svg {
    width: 16px;
    height: 16px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  margin-top: 12px;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.dialog-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 96px;

  &.secondary {
    background: #f3f4f6;
    color: #374151;

    &:hover {
      background: #e5e7eb;
    }
  }

  &.primary {
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);

    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      box-shadow: none;
    }
  }
}
</style>
