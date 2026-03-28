<template>
  <ModalWrapper :visible="visible" @close="handleClose">
    <div class="character-select-dialog">
      <div class="dialog-header">
        <h3 class="dialog-title">选择角色开启新对话</h3>
        <button class="close-btn" @click="handleClose" aria-label="关闭">
          <IconClose />
        </button>
      </div>
      <div class="dialog-body">
        <div v-if="characters.length === 0" class="empty-state">
          <IconCharacter class="empty-icon" />
          <p>暂无角色卡</p>
          <button class="create-btn" @click="handleCreateCharacter">创建角色</button>
        </div>
        <div v-else class="character-grid">
          <div
            v-for="char in characters"
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
            </div>
            <div v-if="selectedCharacterId === char.id" class="selected-indicator">
              <IconCheck />
            </div>
          </div>
        </div>
      </div>
      <div class="dialog-footer">
        <button class="dialog-btn secondary" @click="handleClose">取消</button>
        <button class="dialog-btn primary" :disabled="!selectedCharacterId" @click="handleConfirm">
          开启对话
        </button>
      </div>
    </div>
  </ModalWrapper>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ModalWrapper } from '@/components/common'
import { IconClose, IconCharacter, IconCheck } from '@/components/icons'
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

watch(
  () => props.visible,
  newVisible => {
    if (newVisible) {
      selectedCharacterId.value = ''
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
  width: 480px;
  max-width: 90vw;
  background: white;
  border-radius: 16px;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;

  &:hover {
    background: #f3f4f6;
    color: #374151;
  }

  svg {
    width: 20px;
    height: 20px;
  }
}

.dialog-body {
  padding: 24px;
  max-height: 400px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 24px;
  text-align: center;

  .empty-icon {
    width: 48px;
    height: 48px;
    color: #d1d5db;
  }

  p {
    margin: 0;
    font-size: 14px;
    color: #6b7280;
  }
}

.create-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: white;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
  }
}

.character-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.character-card-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f9fafb;
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #f3f4f6;
    border-color: #e5e7eb;
  }

  &.selected {
    background: #ede9fe;
    border-color: #7c3aed;
  }
}

.card-avatar {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
}

.card-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-nickname {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-indicator {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #7c3aed;
  border-radius: 50%;
  color: white;
  flex-shrink: 0;

  svg {
    width: 14px;
    height: 14px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

.dialog-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

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

    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}
</style>
