<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="visible" class="toast-container" :class="`toast-${type}`">
        <IconSuccess v-if="type === 'success'" class="toast-icon" />
        <IconError v-else-if="type === 'error'" class="toast-icon" />
        <IconWarning v-else-if="type === 'warning'" class="toast-icon" />
        <IconInfo v-else class="toast-icon" />
        <span class="toast-message">{{ message }}</span>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { watch, onUnmounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { IconSuccess, IconError, IconWarning, IconInfo } from '@/components/icons'

const { visible, message, type, hide } = useToast()

watch(visible, isVisible => {
  if (isVisible) {
    document.body.style.overflow = ''
  }
})

onUnmounted(() => {
  hide()
})
</script>

<style lang="scss" scoped>
.toast-container {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  z-index: 4000;
  max-width: 400px;

  &.toast-success {
    background: #10b981;
    color: #ffffff;
  }

  &.toast-error {
    background: #ef4444;
    color: #ffffff;
  }

  &.toast-warning {
    background: #f59e0b;
    color: #ffffff;
  }

  &.toast-info {
    background: #3b82f6;
    color: #ffffff;
  }
}

.toast-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.toast-message {
  line-height: 1.4;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>
