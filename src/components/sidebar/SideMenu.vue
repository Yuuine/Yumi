<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="avatar">
        <el-avatar :size="64" src="/yumi-avatar.svg">Y</el-avatar>
      </div>
      <h2 class="character-name">{{ roleName }}</h2>
      <p class="character-desc">你的AI伴侣</p>
    </div>

    <StatsPanel :conversation-count="conversationCount" :memory-count="memoryCount" />

    <div class="sidebar-menu">
      <el-menu :default-active="activeMenu" router>
        <el-menu-item index="/">
          <el-icon><ChatDotRound /></el-icon>
          <span>对话</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <span>角色设定</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound, User, Setting } from '@element-plus/icons-vue'
import StatsPanel from './StatsPanel.vue'

interface Props {
  roleName: string
  conversationCount: number
  memoryCount: number
  activeMenu: string
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
.sidebar {
  width: 260px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color, #e4e7ed);
  display: flex;
  flex-direction: column;
  padding: 20px;

  .sidebar-header {
    text-align: center;
    padding: 20px 0;

    .avatar {
      margin-bottom: 12px;
    }

    .character-name {
      font-size: 20px;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 4px;
    }

    .character-desc {
      font-size: 13px;
      color: var(--text-secondary);
      margin: 0;
    }
  }

  .sidebar-menu {
    flex: 1;
    margin-top: 12px;

    :deep(.el-menu) {
      border: none;
      background: transparent;
    }

    :deep(.el-menu-item) {
      border-radius: 8px;
      margin: 4px 0;

      &.is-active {
        background: var(--el-color-primary-light-9);
      }
    }
  }
}
</style>
