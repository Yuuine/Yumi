<template>
  <div class="empty-state">
    <div class="empty-icon">
      <el-icon :size="64"><ChatDotRound /></el-icon>
    </div>
    <h4>开始和 {{ roleName }} 聊天吧</h4>
    <p>我是一个温暖、善解人意的AI伴侣，随时准备倾听你的心声</p>
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound } from '@element-plus/icons-vue'

interface Props {
  roleName: string
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);

  .empty-icon {
    margin-bottom: 20px;
    color: var(--el-color-primary-light-3);
  }

  h4 {
    margin: 0 0 8px;
    color: var(--text-primary);
  }

  p {
    margin: 0;
    font-size: 14px;
  }
}
</style>
