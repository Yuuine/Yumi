<template>
  <Dialog
    v-model="localVisible"
    title="选择角色"
    size="medium"
    @confirm="handleConfirm"
    @cancel="handleCancel"
    @close="handleClose"
    :showIcon="false"
    :showCancel="true"
    :showClose="true"
  >
    <div class="character-selector">
      <div v-if="characters.length === 0" class="empty-state">
        <p>暂无角色卡</p>
      </div>
      <div v-else class="character-grid">
        <div
          v-for="char in characters"
          :key="char.id"
          class="character-card"
          :class="{ selected: selectedCharacterId === char.id }"
          @click="selectCharacter(char.id)"
        >
          <div class="character-avatar">{{ (char.name || '未命名')[0] }}</div>
          <div class="character-info">
            <div class="character-name">{{ char.name || '未命名角色' }}</div>
            <div class="character-desc">{{ char.roleOverview?.slice(0, 50) || '暂无描述' }}{{ char.roleOverview?.length > 50 ? '...' : '' }}</div>
          </div>
        </div>
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAccountStore } from '@/stores'
import Dialog from '@/components/common/Dialog.vue'
import { logger } from '@/utils/logger'
import type { AccountCharacter } from '@/types/character'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', characterId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const accountStore = useAccountStore()
const localVisible = ref(props.modelValue)
const characters = ref<AccountCharacter[]>([])
const selectedCharacterId = ref<string | null>(null)

async function loadCharacters() {
  try {
    characters.value = await accountStore.loadCharacters()
    if (characters.value.length > 0) {
      selectedCharacterId.value = characters.value[0].id
    }
  } catch (error) {
    logger.error('CharacterSelector', 'Failed to load characters', error)
  }
}

function selectCharacter(charId: string) {
  selectedCharacterId.value = charId
}

function handleConfirm() {
  if (selectedCharacterId.value) {
    emit('confirm', selectedCharacterId.value)
  }
  emit('update:modelValue', false)
}

function handleCancel() {
  emit('update:modelValue', false)
}

function handleClose() {
  emit('update:modelValue', false)
}

watch(
  () => props.modelValue,
  async (newVal) => {
    localVisible.value = newVal
    if (newVal) {
      await loadCharacters()
    }
  }
)

watch(localVisible, (newVal) => {
  emit('update:modelValue', newVal)
})
</script>

<style lang="scss" scoped>
.character-selector {
  padding: 8px 0;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #9ca3af;
}

.character-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.character-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: #d1d5db;
    background: #f9fafb;
  }

  &.selected {
    border-color: #3b82f6;
    background: #eff6ff;
  }
}

.character-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: 600;
  flex-shrink: 0;
  text-transform: uppercase;
}

.character-info {
  flex: 1;
  min-width: 0;
}

.character-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.character-desc {
  font-size: 12px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>
