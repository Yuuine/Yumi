<template>
  <div class="loading-state">
    <div class="loading-spinner"></div>
    <span v-if="text" class="loading-text">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  text?: string
}

withDefaults(defineProps<Props>(), {
  text: '加载中...',
})
</script>

<style lang="scss" scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  gap: 16px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: loading-spin 0.8s linear infinite;
}

.loading-text {
  font-size: 14px;
  color: #6b7280;
}

@keyframes loading-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
