<template>
  <Teleport to="body">
    <Transition name="loading-fade">
      <div v-if="visible" class="loading-overlay">
        <div class="loading-content">
          <div class="loading-spinner"></div>
          <span v-if="text" class="loading-text">{{ text }}</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
interface Props {
  visible: boolean
  text?: string
}

withDefaults(defineProps<Props>(), {
  text: '加载中...',
})
</script>

<style lang="scss" scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: #ffffff;
  padding: 32px 48px;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: loading-spin 0.8s linear infinite;
}

.loading-text {
  font-size: 15px;
  color: #374151;
  font-weight: 500;
}

@keyframes loading-spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity 0.2s ease;
}

.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}
</style>
