<template>
  <div class="auto-resize-textarea-wrapper">
    <textarea
      ref="textareaRef"
      v-model="internalValue"
      @input="handleInput"
      @focus="isFocused = true"
      @blur="isFocused = false"
      class="auto-resize-textarea"
      :style="wrapperStyle"
      :placeholder="placeholder"
    ></textarea>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'

interface Props {
  modelValue: string
  minHeight?: number
  maxHeight?: number
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  minHeight: 48,
  maxHeight: 200,
  placeholder: '',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const isFocused = ref(false)
const internalValue = ref(props.modelValue)

watch(
  () => props.modelValue,
  newVal => {
    internalValue.value = newVal
    nextTick(() => adjustHeight())
  }
)

function handleInput() {
  emit('update:modelValue', internalValue.value)
  adjustHeight()
}

const wrapperStyle = computed(() => ({
  minHeight: `${props.minHeight}px`,
  maxHeight: `${props.maxHeight}px`,
}))

function adjustHeight() {
  if (!textareaRef.value) return

  textareaRef.value.style.height = 'auto'
  const scrollHeight = textareaRef.value.scrollHeight

  if (scrollHeight <= props.maxHeight) {
    textareaRef.value.style.height = `${scrollHeight}px`
  } else {
    textareaRef.value.style.height = `${props.maxHeight}px`
  }
}

onMounted(() => {
  nextTick(() => adjustHeight())
})
</script>

<style scoped lang="scss">
.auto-resize-textarea-wrapper {
  position: relative;
  width: 100%;
}

.auto-resize-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 18px;
  font-family: inherit;
  background: #ffffff;
  color: #111827;
  line-height: 1.6;
  resize: none;
  overflow-y: auto;
  transition: all 0.15s ease;

  &::placeholder {
    color: #9ca3af;
  }

  &:hover {
    border-color: #9ca3af;
  }

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: #f3f4f6;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;
    transition: background 0.2s ease;

    &:hover {
      background: #9ca3af;
    }
  }
}
</style>
