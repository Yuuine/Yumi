<template>
  <div class="conversation-pair-input-wrapper">
    <div class="conversation-pairs-container">
      <div v-for="(pair, index) in pairs" :key="index" class="conversation-pair-item">
        <div class="conversation-pair-content" @click="toggleExpand(index)">
          <div class="conversation-message" :class="{ 'message-expanded': expandedPairs[index] }">
            <span class="message-role">User:</span>
            <span class="message-text">{{ pair.user }}</span>
          </div>
          <div class="conversation-message" :class="{ 'message-expanded': expandedPairs[index] }">
            <span class="message-role">Assistant:</span>
            <span class="message-text">{{ pair.assistant }}</span>
          </div>
        </div>
        <button type="button" class="pair-remove" @click="removePair(index)" aria-label="移除">
          <svg class="pair-remove-icon" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </div>

      <div class="add-pair-container" v-if="showAddForm">
        <div class="add-pair-form">
          <div class="form-group">
            <label class="form-label">User</label>
            <textarea
              v-model="newPair.user"
              class="pair-textarea"
              placeholder="输入用户消息..."
              rows="2"
            ></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Assistant</label>
            <textarea
              v-model="newPair.assistant"
              class="pair-textarea"
              placeholder="输入助手回复..."
              rows="3"
            ></textarea>
          </div>
          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="cancelAdd">取消</button>
            <button type="button" class="btn-add" @click="addPair" :disabled="!canAdd">添加</button>
          </div>
        </div>
      </div>

      <button v-else type="button" class="add-pair-button" @click="showAddForm = true">
        <svg class="add-icon" viewBox="0 0 20 20" fill="currentColor">
          <path
            fill-rule="evenodd"
            d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
            clip-rule="evenodd"
          />
        </svg>
        <span>添加对话示例</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, reactive } from 'vue'

interface ConversationPair {
  user: string
  assistant: string
}

interface Props {
  modelValue: string | ConversationPair[]
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | ConversationPair[]): void
}>()

const pairs = ref<ConversationPair[]>([])
const showAddForm = ref(false)
const newPair = ref<ConversationPair>({
  user: '',
  assistant: '',
})
const expandedPairs = reactive<Record<number, boolean>>({})

const canAdd = computed(() => {
  return newPair.value.user.trim() && newPair.value.assistant.trim()
})

function toggleExpand(index: number): void {
  expandedPairs[index] = !expandedPairs[index]
}

function parseConversationPairs(value: string): ConversationPair[] {
  const result: ConversationPair[] = []
  if (!value) return result

  const regex = /User:\s*([\s\S]*?)\s*Assistant:\s*([\s\S]*?)(?=\n\nUser:|$)/g
  let match

  while ((match = regex.exec(value)) !== null) {
    const user = match[1].trim()
    const assistant = match[2].trim()
    if (user && assistant) {
      result.push({ user, assistant })
    }
  }

  return result
}

function serializeConversationPairs(pairsList: ConversationPair[]): string {
  return pairsList.map(pair => `User: ${pair.user}\nAssistant: ${pair.assistant}`).join('\n\n')
}

function initializePairs() {
  if (Array.isArray(props.modelValue)) {
    pairs.value = props.modelValue
  } else {
    pairs.value = parseConversationPairs(props.modelValue)
  }
}

initializePairs()

watch(
  () => props.modelValue,
  () => {
    initializePairs()
  }
)

function addPair() {
  if (canAdd.value) {
    pairs.value.push({
      user: newPair.value.user.trim(),
      assistant: newPair.value.assistant.trim(),
    })
    newPair.value = { user: '', assistant: '' }
    showAddForm.value = false
    updateModelValue()
  }
}

function cancelAdd() {
  newPair.value = { user: '', assistant: '' }
  showAddForm.value = false
}

function removePair(index: number) {
  pairs.value.splice(index, 1)
  updateModelValue()
}

function updateModelValue() {
  if (Array.isArray(props.modelValue)) {
    emit('update:modelValue', pairs.value)
  } else {
    emit('update:modelValue', serializeConversationPairs(pairs.value))
  }
}
</script>

<style scoped lang="scss">
.conversation-pair-input-wrapper {
  width: 100%;
}

.conversation-pairs-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  transition: all 0.15s ease;

  &:hover {
    border-color: #9ca3af;
  }

  &:focus-within {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }
}

.conversation-pair-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  transition: all 0.15s ease;

  &:hover {
    background: #e5e7eb;
  }
}

.conversation-pair-content {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.conversation-message {
  display: flex;
  gap: 6px;
  margin-bottom: 4px;
  font-size: 17px;
  line-height: 1.5;

  &:last-child {
    margin-bottom: 0;
  }

  &:not(.message-expanded) .message-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &.message-expanded .message-text {
    white-space: pre-wrap;
    word-break: break-word;
  }
}

.message-role {
  font-weight: 600;
  color: #374151;
  flex-shrink: 0;
}

.message-text {
  color: #4b5563;
}

.pair-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
  border: none;
  background: transparent;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: #6b7280;
  flex-shrink: 0;

  &:hover {
    background: #d1d5db;
    color: #374151;
  }
}

.pair-remove-icon {
  width: 14px;
  height: 14px;
}

.add-pair-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px dashed #d1d5db;
  border-radius: 4px;
  background: transparent;
  color: #6b7280;
  font-size: 17px;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    border-color: #3b82f6;
    color: #3b82f6;
    background: #eff6ff;
  }
}

.add-icon {
  width: 16px;
  height: 16px;
}

.add-pair-container {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 12px;
  background: #f9fafb;
}

.add-pair-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  font-size: 16px;
  font-weight: 500;
  color: #374151;
}

.pair-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 17px;
  font-family: inherit;
  background: #ffffff;
  resize: vertical;
  line-height: 1.5;
  transition: all 0.15s ease;

  &:hover {
    border-color: #9ca3af;
  }

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-cancel,
.btn-add {
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 17px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-cancel {
  border: 1px solid #d1d5db;
  background: #ffffff;
  color: #374151;

  &:hover {
    background: #f3f4f6;
  }
}

.btn-add {
  border: none;
  background: #3b82f6;
  color: #ffffff;

  &:hover {
    background: #2563eb;
  }

  &:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }
}
</style>
