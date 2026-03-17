<template>
  <div
    class="sidebar-nav"
    :class="{ expanded: isExpanded }"
    @mouseenter="expandSidebar"
    @mouseleave="collapseSidebar"
  >
    <nav class="sidebar-menu">
      <button
        v-for="item in menuItems"
        :key="item.id"
        class="menu-item"
        @click="handleMenuClick(item.id)"
        :title="item.label"
      >
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" v-html="item.iconSvg"></svg>
        <span class="menu-label">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface MenuItem {
  id: string
  label: string
  iconSvg: string
}

const isExpanded = ref(false)

const menuItems: MenuItem[] = [
  {
    id: 'chat',
    label: '对话',
    iconSvg: '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  },
  {
    id: 'profile',
    label: '角色设定',
    iconSvg: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>',
  },
  {
    id: 'settings',
    label: '设置',
    iconSvg: '<circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  },
  {
    id: 'documents',
    label: '功能A',
    iconSvg: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  },
  {
    id: 'folder',
    label: '功能B',
    iconSvg: '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  },
]

function expandSidebar() {
  isExpanded.value = true
}

function collapseSidebar() {
  isExpanded.value = false
}

function handleMenuClick(menuId: string) {
  switch (menuId) {
    case 'chat':
      // TODO: 实现对话导航逻辑
      console.log('[模拟] 点击菜单：对话')
      break
    case 'profile':
      // TODO: 实现角色设定导航逻辑
      console.log('[模拟] 点击菜单：角色设定')
      break
    case 'settings':
      // TODO: 实现设置导航逻辑
      console.log('[模拟] 点击菜单：设置')
      break
    case 'documents':
      // TODO: 实现功能A逻辑
      console.log('[模拟] 点击菜单：功能A')
      break
    case 'folder':
      // TODO: 实现功能B逻辑
      console.log('[模拟] 点击菜单：功能B')
      break
    default:
      // TODO: 实现其他菜单项逻辑
      console.log('[模拟] 点击菜单：', menuId)
  }
}
</script>

<style lang="scss" scoped>
.sidebar-nav {
  position: fixed;
  top: 50%;
  left: 16px;
  transform: translateY(-50%);
  z-index: 100;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 8px;
  width: 56px;
  transition: width 0.25s ease;

  &.expanded {
    width: 160px;
  }
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-primary);
  text-align: left;

  &:hover {
    background: var(--bg-hover);
  }

  &:active {
    background: var(--bg-tertiary);
  }

  .menu-label {
    font-size: 14px;
    white-space: nowrap;
    opacity: 0;
    max-width: 0;
    overflow: hidden;
    transition: all 0.2s ease;
  }
}

.menu-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.sidebar-nav.expanded .menu-item .menu-label {
  opacity: 1;
  max-width: 100px;
}
</style>
