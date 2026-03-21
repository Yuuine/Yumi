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
        <component :is="item.icon" class="menu-icon" />
        <span class="menu-label">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { IconChat, IconModels, IconCharacter } from '@/components/icons'
import IconSettings from '@/components/icons/IconSettings.vue'

interface MenuItem {
  id: string
  label: string
  icon: ReturnType<typeof markRaw>
}

const emit = defineEmits<{
  openModels: []
  openCharacter: []
  openSettings: []
}>()

const router = useRouter()
const isExpanded = ref(false)

const menuItems: MenuItem[] = [
  {
    id: 'chat',
    label: '对话',
    icon: markRaw(IconChat),
  },
  {
    id: 'character',
    label: '角色',
    icon: markRaw(IconCharacter),
  },
  {
    id: 'models',
    label: '模型',
    icon: markRaw(IconModels),
  },
  {
    id: 'settings',
    label: '设置',
    icon: markRaw(IconSettings),
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

  if (menuId === 'character') {
    emit('openCharacter')
    return
  }

  if (menuId === 'settings') {
    emit('openSettings')
    return
  }

  const routeMap: Record<string, string> = {
    chat: '/',
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
