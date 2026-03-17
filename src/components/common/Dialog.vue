<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="modelValue" class="dialog-overlay" @click.self="handleOverlayClick">
        <div class="dialog-container" :class="[`dialog-${type}`, `dialog-${size}`]">
          <div class="dialog-header">
            <div class="dialog-icon" v-if="showIcon">
              <IconSuccess v-if="type === 'success'" />
              <IconWarning v-else-if="type === 'warning'" />
              <IconError v-else-if="type === 'error'" />
              <IconInfo v-else />
            </div>
            <h3 class="dialog-title">{{ title }}</h3>
            <button v-if="showClose" class="dialog-close" @click="handleClose" aria-label="关闭">
              <IconClose />
            </button>
          </div>

          <div class="dialog-body">
            <p class="dialog-message">{{ message }}</p>
            <div v-if="$slots.default" class="dialog-content">
              <slot></slot>
            </div>
          </div>

          <div class="dialog-footer">
            <button v-if="showCancel" class="dialog-btn secondary" @click="handleCancel">
              {{ cancelText }}
            </button>
            <button class="dialog-btn primary" :class="`btn-${type}`" @click="handleConfirm">
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { IconClose, IconSuccess, IconWarning, IconError, IconInfo } from '@/components/icons'

type DialogType = 'info' | 'success' | 'warning' | 'error'
type DialogSize = 'small' | 'medium' | 'large'

const props = withDefaults(
  defineProps<{
    modelValue?: boolean
    title?: string
    message?: string
    type?: DialogType
    size?: DialogSize
    showIcon?: boolean
    showClose?: boolean
    showCancel?: boolean
    closeOnClickOverlay?: boolean
    confirmText?: string
    cancelText?: string
  }>(),
  {
    modelValue: false,
    title: '提示',
    message: '',
    type: 'info',
    size: 'medium',
    showIcon: true,
    showClose: true,
    showCancel: false,
    closeOnClickOverlay: true,
    confirmText: '确定',
    cancelText: '取消',
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  cancel: []
  close: []
}>()

function handleClose() {
  emit('update:modelValue', false)
  emit('close')
}

function handleConfirm() {
  emit('confirm')
  handleClose()
}

function handleCancel() {
  emit('cancel')
  handleClose()
}

function handleOverlayClick() {
  if (props.closeOnClickOverlay) {
    handleClose()
  }
}
</script>

<style lang="scss" scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}

.dialog-container {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  overflow: hidden;

  &.dialog-small {
    width: 320px;
    max-width: 90vw;
  }

  &.dialog-medium {
    width: 420px;
    max-width: 90vw;
  }

  &.dialog-large {
    width: 560px;
    max-width: 90vw;
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  padding: 20px 24px 16px;
  gap: 12px;
}

.dialog-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;

  svg {
    width: 100%;
    height: 100%;
  }
}

.dialog-success .dialog-icon {
  color: #10b981;
}

.dialog-warning .dialog-icon {
  color: #f59e0b;
}

.dialog-error .dialog-icon {
  color: #ef4444;
}

.dialog-info .dialog-icon {
  color: #3b82f6;
}

.dialog-title {
  flex: 1;
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: #1f2937;
}

.dialog-close {
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
  padding: 0 24px 20px;
}

.dialog-message {
  margin: 0;
  font-size: var(--font-size-xs);
  line-height: 1.6;
  color: #4b5563;
}

.dialog-content {
  margin-top: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.dialog-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: var(--font-size-xs);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &.secondary {
    background: #ffffff;
    color: #374151;
    border: 1px solid #d1d5db;

    &:hover {
      background: #f9fafb;
      border-color: #9ca3af;
    }
  }

  &.primary {
    background: #3b82f6;
    color: #ffffff;

    &:hover {
      background: #2563eb;
    }
  }

  &.btn-success {
    background: #10b981;

    &:hover {
      background: #059669;
    }
  }

  &.btn-warning {
    background: #f59e0b;

    &:hover {
      background: #d97706;
    }
  }

  &.btn-error {
    background: #ef4444;

    &:hover {
      background: #dc2626;
    }
  }
}

.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.2s ease;

  .dialog-container {
    transition:
      transform 0.2s ease,
      opacity 0.2s ease;
  }
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;

  .dialog-container {
    transform: scale(0.95) translateY(-10px);
    opacity: 0;
  }
}
</style>
