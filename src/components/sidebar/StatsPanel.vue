<template>
  <div class="stats-panel">
    <div class="stat-item">
      <span class="stat-value">{{ conversationCount }}</span>
      <span class="stat-label">对话轮次</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">{{ memoryCount }}</span>
      <span class="stat-label">记忆条数</span>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  conversationCount: number
  memoryCount: number
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
.stats-panel {
  display: flex;
  justify-content: space-around;
  padding: 16px 0;
  margin: 12px 0;
  background: var(--bg-primary);
  border-radius: 8px;

  .stat-item {
    text-align: center;

    .stat-value {
      display: block;
      font-size: var(--font-size-xxl);
      font-weight: 600;
      color: var(--el-color-primary);
    }

    .stat-label {
      font-size: var(--font-size-xs);
      color: var(--text-secondary);
    }
  }
}
</style>
