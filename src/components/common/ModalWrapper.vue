<template>
  <Teleport to="body">
    <Transition name="modal-wrapper">
      <div v-if="visible" class="modal-wrapper-overlay" @click.self="handleOverlayClick">
        <div class="modal-wrapper-container" :class="containerClass">
          <div class="modal-wrapper-header" v-if="$slots.header || title">
            <slot name="header">
              <h2 class="modal-wrapper-title">{{ title }}</h2>
            </slot>
            <button
              v-if="showClose"
              class="modal-wrapper-close"
              @click="handleClose"
              aria-label="关闭"
            >
              <IconClose />
            </button>
          </div>
          <div class="modal-wrapper-body">
            <slot></slot>
          </div>
          <div v-if="$slots.footer" class="modal-wrapper-footer">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { IconClose } from '@/components/icons'

interface Props {
  visible: boolean
  title?: string
  size?: 'small' | 'medium' | 'large' | 'xlarge'
  showClose?: boolean
  closeOnClickOverlay?: boolean
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  size: 'medium',
  showClose: true,
  closeOnClickOverlay: true,
  customClass: '',
})

const emit = defineEmits<{
  close: []
}>()

const containerClass = computed(() => {
  return [
    `modal-wrapper-${props.size}`,
    props.customClass,
  ]
})

function handleClose() {
  emit('close')
}

function handleOverlayClick() {
  if (props.closeOnClickOverlay) {
    handleClose()
  }
}
</script>

<style lang="scss" scoped>
.modal-wrapper-overlay {
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

.modal-wrapper-container {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  overflow: hidden;

  &.modal-wrapper-small {
    width: 360px;
    max-width: 90vw;
  }

  &.modal-wrapper-medium {
    width: 480px;
    max-width: 90vw;
  }

  &.modal-wrapper-large {
    width: 640px;
    max-width: 90vw;
  }

  &.modal-wrapper-xlarge {
    width: 800px;
    max-width: 95vw;
  }
}

.modal-wrapper-header {
  display: flex;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.modal-wrapper-title {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.modal-wrapper-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #9ca3af;
  transition: all 0.2s;
  flex-shrink: 0;
  margin-left: 12px;

  &:hover {
    background: #f3f4f6;
    color: #374151;
  }

  svg {
    width: 20px;
    height: 20px;
  }
}

.modal-wrapper-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;

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

.modal-wrapper-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
}

.modal-wrapper-enter-active,
.modal-wrapper-leave-active {
  transition: opacity 0.2s ease;

  .modal-wrapper-container {
    transition:
      transform 0.2s ease,
      opacity 0.2s ease;
  }
}

.modal-wrapper-enter-from,
.modal-wrapper-leave-to {
  opacity: 0;

  .modal-wrapper-container {
    transform: scale(0.95) translateY(-10px);
    opacity: 0;
  }
}
</style>
