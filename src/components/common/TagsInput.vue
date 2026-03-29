<template>
  <div class="tags-input-wrapper">
    <div class="tags-container">
      <span v-for="(tag, index) in tags" :key="index" class="tag-item">
        <span class="tag-text">{{ tag }}</span>
        <button type="button" class="tag-remove" @click="removeTag(index)" aria-label="移除">
          <svg class="tag-remove-icon" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </span>
      <input
        ref="inputRef"
        v-model="inputValue"
        @keydown.enter.prevent="handleKeyDown"
        @keydown.backspace="handleBackspace"
        @blur="handleBlur"
        class="tag-input"
        type="text"
        :placeholder="placeholder"
        autocomplete="off"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'

interface Props {
  modelValue: string | string[]
  separator?: string
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  separator: ',',
  placeholder: '输入后按回车添加',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | string[]): void
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const inputValue = ref('')

function parseBracketContent(value: string): string[] {
  const result: string[] = []
  const regex = /【([^】]+)】/g
  let match

  while ((match = regex.exec(value)) !== null) {
    const content = match[1].trim()
    if (content) {
      result.push(content)
    }
  }

  return result
}

function initializeTags() {
  if (Array.isArray(props.modelValue)) {
    tags.value = props.modelValue.filter(t => t.trim())
  } else {
    const bracketTags = parseBracketContent(props.modelValue)
    if (bracketTags.length > 0) {
      tags.value = bracketTags
    } else {
      tags.value = props.modelValue.split(props.separator).filter(t => t.trim())
    }
  }
}

const tags = ref<string[]>([])

initializeTags()

watch(
  () => props.modelValue,
  () => {
    initializeTags()
  }
)

function addTagsFromInput(value: string) {
  const trimmedValue = value.trim()
  if (!trimmedValue) return

  const bracketTags = parseBracketContent(trimmedValue)
  if (bracketTags.length > 0) {
    bracketTags.forEach(tag => {
      if (!tags.value.includes(tag)) {
        tags.value.push(tag)
      }
    })
  } else {
    tags.value.push(trimmedValue)
  }
  inputValue.value = ''
  updateModelValue()
}

function handleKeyDown() {
  addTagsFromInput(inputValue.value)
}

function handleBackspace() {
  if (!inputValue.value && tags.value.length > 0) {
    tags.value.pop()
    updateModelValue()
  }
}

function handleBlur() {
  addTagsFromInput(inputValue.value)
}

function removeTag(index: number) {
  tags.value.splice(index, 1)
  updateModelValue()
  nextTick(() => {
    inputRef.value?.focus()
  })
}

function updateModelValue() {
  if (Array.isArray(props.modelValue)) {
    emit('update:modelValue', tags.value)
  } else {
    emit('update:modelValue', tags.value.join(props.separator))
  }
}
</script>

<style scoped lang="scss">
.tags-input-wrapper {
  width: 100%;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
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

.tag-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #f3f4f6;
  color: #374151;
  border-radius: 4px;
  font-size: 17px;
  font-weight: 400;
  transition: all 0.15s ease;

  &:hover {
    background: #e5e7eb;
  }
}

.tag-text {
  user-select: none;
}

.tag-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 1px;
  border: none;
  background: transparent;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: #6b7280;

  &:hover {
    background: #d1d5db;
    color: #374151;
  }
}

.tag-remove-icon {
  width: 12px;
  height: 12px;
}

.tag-input {
  flex: 1;
  min-width: 120px;
  border: none;
  outline: none;
  background: transparent;
  font-size: 18px;
  color: #111827;
  font-family: inherit;

  &::placeholder {
    color: #9ca3af;
  }
}
</style>
