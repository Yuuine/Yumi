<template>
  <div class="chat-input-wrapper">
    <div class="chat-input-container">
      <div class="input-field">
        <textarea
          v-model="inputText"
          class="input-textarea"
          placeholder="你好啊！"
          rows="1"
          @keydown.enter.exact.prevent="handleSend"
          @input="adjustHeight"
          ref="textareaRef"
        ></textarea>
        <Transition name="fade">
          <button v-if="hasContent" class="send-btn" @click="handleSend" title="发送消息">
            <svg
              class="send-icon"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M22 2L11 13"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M22 2L15 22L11 13L2 9L22 2Z"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'

const emit = defineEmits<{
  send: [content: string]
}>()

const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const hasContent = computed(() => inputText.value.trim().length > 0)

function adjustHeight() {
  const textarea = textareaRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`
  }
}

function handleSend() {
  const content = inputText.value.trim()
  if (!content) return

  console.log(`[模拟] 发送消息：${content}`)
  // TODO: 连接发送API
  emit('send', content)

  inputText.value = ''
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
    }
  })
}
</script>

<style lang="scss" scoped>
.chat-input-wrapper {
  position: fixed;
  bottom: 0;
  left: 64px;
  right: 0;
  display: flex;
  justify-content: center;
  padding: 16px 24px 60px;
  background: linear-gradient(to top, #ffffff 80%, transparent);
  pointer-events: none;
}

.chat-input-container {
  width: 100%;
  max-width: 816px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #d0d0d0;
  border-radius: 28px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  pointer-events: auto;
}

.input-field {
  position: relative;
  padding: 16px 20px;
  min-height: 60px;
}

.input-textarea {
  display: block;
  width: 100%;
  padding-right: 52px;
  border: none;
  outline: none;
  background: transparent;
  font-size: 18px;
  line-height: 1.5;
  resize: none;
  max-height: 160px;
  color: var(--text-primary);
  font-family: inherit;
  margin: 0;

  &::placeholder {
    color: var(--text-placeholder);
  }
}

.send-btn {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: #000000;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #333333;
    transform: translateY(-50%) scale(1.05);
  }

  &:active {
    transform: translateY(-50%) scale(0.95);
  }
}

.send-icon {
  width: 18px;
  height: 18px;
  color: #ffffff;
}

.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-50%) scale(0.8);
}
</style>
