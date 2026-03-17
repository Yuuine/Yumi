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
        <svg
          class="menu-icon"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          v-html="item.iconSvg"
        ></svg>
        <span class="menu-label">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

interface MenuItem {
  id: string
  label: string
  iconSvg: string
}

const emit = defineEmits<{
  openModels: []
}>()

const router = useRouter()
const isExpanded = ref(false)

const menuItems: MenuItem[] = [
  {
    id: 'chat',
    label: '对话',
    iconSvg:
      '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  },
  {
    id: 'models',
    label: '模型',
    iconSvg:
      '<rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M9 9h6M9 13h6M9 17h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  },
]

function expandSidebar() {
  isExpanded.value = true
}

function collapseSidebar() {
  isExpanded.value = false
}

function handleMenuClick(menuId: string) {
  if (menuId === 'models') {
    emit('openModels')
    return
  }

  const routeMap: Record<string, string> = {
    chat: '/',
    settings: '/settings',
  }

  const path = routeMap[menuId]
  if (path) {
    router.push(path)
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
