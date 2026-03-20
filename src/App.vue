<template>
  <div class="app-container" :class="themeClass">
    <el-config-provider :locale="zhCn">
      <div v-if="!accountStore.isInitialized" class="init-loading">
        <div class="loading-spinner"></div>
        <span>正在初始化...</span>
      </div>
      <router-view v-else />
    </el-config-provider>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useAccountStore, useChatStore, useModelsStore } from '@/stores'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { ElMessage } from 'element-plus'

const DEFAULT_ACCOUNT_CREATED_TOAST_KEY = 'yumi_show_default_account_created_toast'

const settingsStore = useSettingsStore()
const accountStore = useAccountStore()
const chatStore = useChatStore()
const modelsStore = useModelsStore()
const themeClass = computed(() => `theme-${settingsStore.theme}`)

onMounted(async () => {
  await accountStore.initialize()
  if (sessionStorage.getItem(DEFAULT_ACCOUNT_CREATED_TOAST_KEY) === '1') {
    sessionStorage.removeItem(DEFAULT_ACCOUNT_CREATED_TOAST_KEY)
    ElMessage.success('已创建新默认角色')
  }
})

watch(
  () => accountStore.currentAccountId,
  async accountId => {
    chatStore.clearMessages()
    if (!accountId) {
      return
    }
    chatStore.currentUserId = accountId
    await Promise.all([
      chatStore.loadHistory(),
      modelsStore.loadModels(),
      modelsStore.loadActiveModel(),
    ])
  },
  { immediate: true }
)
</script>

<style lang="scss">
.app-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.init-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  gap: 16px;
  background: var(--bg-primary, #1a1a2e);

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e5e7eb;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  span {
    color: var(--text-secondary, #a0a0a0);
    font-size: 14px;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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
