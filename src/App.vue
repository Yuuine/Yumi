<template>
  <div class="app-container" :class="themeClass">
    <el-config-provider :locale="zhCn">
      <router-view />
    </el-config-provider>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const settingsStore = useSettingsStore()
const themeClass = computed(() => `theme-${settingsStore.theme}`)
</script>

<style lang="scss">
.app-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.theme-dark {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --text-primary: #eaeaea;
  --text-secondary: #a0a0a0;
}

.theme-light {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f7fa;
  --text-primary: #303133;
  --text-secondary: #606266;
}
</style>
