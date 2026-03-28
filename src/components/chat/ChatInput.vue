<template>
  <div :class="['chat-input-wrapper', { 'sidebar-collapsed': sidebarCollapsed }]">
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
      </div>

      <div class="bottom-toolbar">
        <div class="model-switch-wrapper" ref="modelSwitchRef">
          <button
            class="toolbar-btn model-switch-btn"
            :class="{ active: showMenu }"
            @click="toggleMenu"
            :disabled="disabled"
            type="button"
          >
            <span>切换模型</span>
          </button>

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

        <button
          class="toolbar-btn deep-think-btn"
          :class="{ active: isDeepThinking }"
          @click="toggleDeepThinking"
          :disabled="disabled || !deepThinkingAvailable"
          type="button"
          :title="deepThinkingAvailable ? '深度思考' : '当前模型不支持深度思考'"
        >
          <span>深度思考</span>
        </button>

        <Transition name="fade">
          <button
            v-if="hasContent"
            class="send-btn"
            @click="handleSend"
            :disabled="disabled"
            :class="{ 'no-model': !hasAvailableModels }"
            :title="hasAvailableModels ? '发送消息' : '暂无可用模型'"
            type="button"
          >
            <IconArrowUp class="send-icon" />
          </button>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useModelsStore, useAccountStore } from '@/stores'
import { PROVIDER_NAMES, supportsDeepThinking } from '@/constants'
import { IconArrowUp, IconCheck } from '@/components/icons'
import { logger } from '@/utils/logger'
import { useToast } from '@/composables'
import type { ModelConfig } from '@/types'

interface Props {
  disabled?: boolean
  sidebarCollapsed?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  sidebarCollapsed: false,
})

const emit = defineEmits<{
  send: [content: string]
}>()

/** 深度思考开关，由父组件通过 v-model:deepThinking 控制，保证发送时状态一致 */
const isDeepThinking = defineModel<boolean>('deepThinking', { default: false })

const modelsStore = useModelsStore()
const accountStore = useAccountStore()
const toast = useToast()

const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const menuRef = ref<HTMLElement | null>(null)
const modelSwitchRef = ref<HTMLElement | null>(null)
const showMenu = ref(false)
const switchingModelId = ref<string | null>(null)

const hasContent = computed(() => inputText.value.trim().length > 0)

const hasAvailableModels = computed(() => enabledModels.value.length > 0)

const deepThinkingAvailable = computed(() => {
  const active = modelsStore.activeModel
  return !!active && supportsDeepThinking(active.providerId, active.modelName)
})

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
  if (!hasAvailableModels.value) {
    toast.warning('暂无可用模型')
    return
  }
  const content = inputText.value.trim()
  if (!content) return

  emit('send', content)

  inputText.value = ''
  showMenu.value = false
  nextTick(adjustHeight)
}

function toggleMenu() {
  showMenu.value = !showMenu.value
}

function toggleDeepThinking() {
  isDeepThinking.value = !isDeepThinking.value
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
  if (modelSwitchRef.value && !modelSwitchRef.value.contains(event.target as Node)) {
    showMenu.value = false
  }
}

// 切换模型后，若新模型不支持深度思考，则重置状态
watch(
  () => modelsStore.activeModel,
  active => {
    if (
      active &&
      !supportsDeepThinking(active.providerId, active.modelName) &&
      isDeepThinking.value
    ) {
      isDeepThinking.value = false
    }
  },
  { deep: true }
)

onMounted(async () => {
  document.addEventListener('click', handleClickOutside)

  // 等待账号初始化完成后再加载模型
  if (accountStore.isInitialized && accountStore.currentAccountId) {
    await modelsStore.loadModels()
    await modelsStore.loadActiveModel()
  }
})

// 监听账号初始化状态，初始化完成后加载模型
watch(
  () => accountStore.isInitialized,
  async isInitialized => {
    if (isInitialized && accountStore.currentAccountId) {
      await modelsStore.loadModels()
      await modelsStore.loadActiveModel()
    }
  }
)

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style lang="scss" scoped>
.chat-input-wrapper {
  position: fixed;
  bottom: 24px;
  left: 280px;
  right: 0;
  display: flex;
  justify-content: center;
  padding: 0 24px;
  pointer-events: none;
  z-index: 50;
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &.sidebar-collapsed {
    left: 72px;
  }
}

.chat-input-container {
  position: relative;
  width: 100%;
  max-width: 816px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
  pointer-events: auto;
}

.input-field {
  position: relative;
  padding: 16px 20px;
  min-height: 52px;
  display: flex;
  align-items: center;
}

.bottom-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 12px;
  border-top: 1px solid #f3f4f6;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  color: #6b7280;

  &:hover:not(:disabled):not(.active) {
    background: #f9fafb;
    color: #374151;
    border-color: #d1d5db;
  }

  &:hover:not(:disabled).active {
    background: #dbeafe;
    color: #1d4ed8;
    border-color: #2563eb;
  }

  &:active:not(:disabled) {
    transform: scale(0.98);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.active {
    background: #eff6ff;
    color: #2563eb;
    border-color: #3b82f6;
  }
}

.model-switch-wrapper {
  position: relative;
}

.input-textarea {
  display: block;
  width: 100%;
  padding-right: 20px;
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
  margin-left: auto;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: #000000;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    background: #333333;
    transform: scale(1.05);
  }

  &:active:not(:disabled) {
    transform: scale(0.95);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.no-model {
    background: #9ca3af;
    &:hover:not(:disabled) {
      background: #6b7280;
    }
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
  left: 0;
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
