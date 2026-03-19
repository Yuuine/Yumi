<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="deep-thinking-overlay" @click.self="handleClose">
        <div class="deep-thinking-modal">
          <div class="modal-header">
            <h2 class="modal-title">深度思考</h2>
            <button class="close-btn" @click="handleClose" aria-label="关闭" type="button">
              <IconClose />
            </button>
          </div>

          <div class="modal-body">
            <div class="placeholder-content">
              <IconBrain class="placeholder-icon" />
              <p class="placeholder-text">深度思考功能正在开发中，敬请期待</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { IconClose, IconBrain } from '@/components/icons'

interface Props {
  visible: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

function handleClose() {
  emit('close')
}
</script>

<style lang="scss" scoped>
.deep-thinking-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.deep-thinking-modal {
  background: #ffffff;
  border-radius: 12px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;

  .modal-title {
    margin: 0;
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: #333333;
  }
}

.close-btn {
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
    color: #333333;
  }

  svg {
    width: 20px;
    height: 20px;
  }
}

.modal-body {
  padding: 48px 24px;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  color: #9ca3af;
}

.placeholder-text {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;

  .deep-thinking-modal {
    transition:
      transform 0.25s ease,
      opacity 0.25s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .deep-thinking-modal {
    transform: scale(0.95) translateY(-20px);
    opacity: 0;
  }
}
</style>
