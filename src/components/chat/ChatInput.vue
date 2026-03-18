<template>
  <div class="chat-input-wrapper">
    <div class="chat-input-container">
      <div class="input-field">
        <button
          class="plus-btn"
          :class="{ active: showMenu }"
          @click="toggleMenu"
          :disabled="disabled"
          title="更多功能"
          aria-label="更多功能"
        >
          <IconPlus class="plus-icon" />
        </button>

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
            <IconSend class="send-icon" />
          </button>
        </Transition>
      </div>

      <Transition name="menu-fade">
        <div v-if="showMenu" class="dropdown-menu" ref="menuRef">
          <div class="menu-header">
            <span class="menu-title">切换模型</span>
          </div>

          <div class="menu-list">
            <div v-if="enabledModels.length === 0" class="menu-empty">
              暂无可用模型，请先添加并启用模型
            </div>

            <button
              v-for="model in enabledModels"
              :key="model.id"
              class="menu-item"
              :class="{ active: model.id === modelsStore.activeModel?.id }"
              @click="handleSwitchModel(model)"
              :disabled="switchingModelId === model.id"
            >
              <div class="model-info">
                <span class="model-name">{{ model.name }}</span>
                <span class="model-provider">{{ getProviderName(model.providerId) }}</span>
              </div>
              <IconCheck v-if="model.id === modelsStore.activeModel?.id" class="check-icon" />
              <div v-else-if="switchingModelId === model.id" class="loading-spinner"></div>
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useModelsStore } from '@/stores'
import { PROVIDER_NAMES } from '@/constants'
import { IconPlus, IconSend, IconCheck } from '@/components/icons'
import { logger } from '@/utils/logger'
import type { ModelConfig } from '@/types'

interface Props {
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  send: [content: string]
}>()

const modelsStore = useModelsStore()

const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const menuRef = ref<HTMLElement | null>(null)
const showMenu = ref(false)
const switchingModelId = ref<string | null>(null)

const hasContent = computed(() => inputText.value.trim().length > 0)

const enabledModels = computed(() => {
  return modelsStore.models.filter(m => m.isEnabled && m.apiKey)
})

function getProviderName(providerId: string): string {
  return PROVIDER_NAMES[providerId] || providerId
}

function adjustHeight() {
  const textarea = textareaRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`
  }
}

function handleSend() {
  if (props.disabled) return
  const content = inputText.value.trim()
  if (!content) return

  emit('send', content)

  inputText.value = ''
  showMenu.value = false
}

function toggleMenu() {
  showMenu.value = !showMenu.value
}

async function handleSwitchModel(model: ModelConfig) {
  if (model.id === modelsStore.activeModel?.id) {
    showMenu.value = false
    return
  }

  switchingModelId.value = model.id
  try {
    await modelsStore.switchModel(model.id)
    showMenu.value = false
  } catch (error) {
    logger.error('ChatInput', 'Failed to switch model', error)
  } finally {
    switchingModelId.value = null
  }
}

function handleClickOutside(event: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    const plusBtn = document.querySelector('.plus-btn')
    if (plusBtn && !plusBtn.contains(event.target as Node)) {
      showMenu.value = false
    }
  }
}

onMounted(async () => {
  await modelsStore.loadModels()
  await modelsStore.loadActiveModel()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
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
  position: relative;
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
  padding-left: 64px;
  min-height: 60px;
  display: flex;
  align-items: center;
}

.plus-btn {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #666666;

  &:hover:not(:disabled) {
    background: #f3f4f6;
    color: #333333;
  }

  &:active:not(:disabled) {
    transform: translateY(-50%) scale(0.95);
  }

  &.active {
    background: #f3f4f6;
    color: #3b82f6;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.plus-icon {
  width: 20px;
  height: 20px;
  transition: transform 0.2s ease;
}

.plus-btn.active .plus-icon {
  transform: rotate(45deg);
}

.input-textarea {
  display: block;
  width: 100%;
  padding-right: 52px;
  border: none;
  outline: none;
  background: transparent;
  font-size: var(--font-size-lg);
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

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 12px;
  width: 280px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  z-index: 100;
}

.menu-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  background: #fafafa;
}

.menu-title {
  font-size: 13px;
  font-weight: 600;
  color: #333333;
}

.menu-list {
  max-height: 240px;
  overflow-y: auto;
}

.menu-empty {
  padding: 24px 16px;
  text-align: center;
  font-size: 13px;
  color: #9ca3af;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: background 0.15s ease;
  text-align: left;

  &:hover:not(:disabled) {
    background: #f9fafb;
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  &.active {
    background: #eff6ff;
  }
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.model-name {
  font-size: 14px;
  font-weight: 500;
  color: #333333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-provider {
  font-size: 12px;
  color: #9ca3af;
}

.check-icon {
  width: 20px;
  height: 20px;
  color: #3b82f6;
  flex-shrink: 0;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}

.menu-fade-enter-active,
.menu-fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
