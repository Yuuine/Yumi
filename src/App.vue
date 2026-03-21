<template>
  <div class="app-container" :class="themeClass">
    <el-config-provider :locale="zhCn">
      <div v-if="showInitLoading" class="init-loading">
        <div class="loading-spinner"></div>
        <span>正在初始化...</span>
      </div>
      <router-view v-else />
      <Toast />
      <DataSyncDialog ref="dataSyncDialogRef" @confirm="handleDataSyncConfirm" />
    </el-config-provider>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useAccountStore, useChatStore, useModelsStore } from '@/stores'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import Toast from '@/components/common/Toast.vue'
import DataSyncDialog from '@/components/common/DataSyncDialog.vue'
import { useToast } from '@/composables/useToast'
import { userApi } from '@/api/user'
import { logger } from '@/utils/logger'

const toast = useToast()

const DEFAULT_ACCOUNT_CREATED_TOAST_KEY = 'yumi_show_default_account_created_toast'
const ACCOUNTS_KEY = 'yumi_accounts'

const settingsStore = useSettingsStore()
const accountStore = useAccountStore()
const chatStore = useChatStore()
const modelsStore = useModelsStore()
const themeClass = computed(() => `theme-${settingsStore.theme}`)

const showInitLoading = ref(true)
const dataSyncDialogRef = ref<InstanceType<typeof DataSyncDialog>>()

interface LocalAccountsData {
  accounts: Array<{ id: string; displayName: string }>
}

function loadLocalAccounts(): LocalAccountsData | null {
  const stored = localStorage.getItem(ACCOUNTS_KEY)
  if (!stored) return null
  try {
    return JSON.parse(stored)
  } catch {
    return null
  }
}

function showDefaultAccountCreatedToastIfNeeded(): void {
  if (sessionStorage.getItem(DEFAULT_ACCOUNT_CREATED_TOAST_KEY) === '1') {
    sessionStorage.removeItem(DEFAULT_ACCOUNT_CREATED_TOAST_KEY)
    toast.success('已创建新默认角色')
  }
}

async function initializeAccountAndHideLoading(): Promise<void> {
  await accountStore.initialize()
  showInitLoading.value = false
  showDefaultAccountCreatedToastIfNeeded()
}

async function checkDataSync(): Promise<boolean> {
  try {
    const data = loadLocalAccounts()

    if (!data) {
      logger.info('App', 'No local accounts found')
      return true
    }

    const accounts = data.accounts ?? []

    if (accounts.length === 0) {
      logger.info('App', 'Local accounts found but empty')
      return true
    }

    for (const account of accounts) {
      try {
        await userApi.getProfile(account.id)
        logger.info('App', 'Account exists in backend', { accountId: account.id })
        return true
      } catch (_e) {
        logger.info('App', 'Account not found in backend, showing sync dialog', {
          accountId: account.id,
        })
        return false
      }
    }

    return true
  } catch (e) {
    logger.error('App', 'Failed to check data sync', e as Record<string, unknown>)
    return true
  }
}

async function handleDataSyncConfirm(option: 'restart' | 'sync') {
  if (option === 'sync') {
    try {
      const data = loadLocalAccounts()

      if (data) {
        const accounts = data.accounts ?? []

        for (const account of accounts) {
          try {
            await userApi.getProfile(account.id)
          } catch (_e) {
            logger.info('App', 'Creating account in backend', { accountId: account.id })
            await userApi.updateProfile({
              id: account.id,
              roleName: account.displayName,
              preferences: {
                communicationStyle: 'warm',
                topicsOfInterest: ['生活', '工作', '情感'],
                emotionalSupportLevel: 'high',
                responseLength: 'medium',
              },
            })
          }
        }
      }

      await initializeAccountAndHideLoading()
      toast.success('数据同步成功')
    } catch (e) {
      logger.error('App', 'Failed to sync data', e as Record<string, unknown>)
      toast.error('数据同步失败')
      await initializeAccountAndHideLoading()
    }
  } else if (option === 'restart') {
    try {
      const data = loadLocalAccounts()

      if (data) {
        const accounts = data.accounts ?? []

        for (const account of accounts) {
          const accountStorageKey = `yumi_account_${account.id}`
          localStorage.removeItem(accountStorageKey)
        }

        localStorage.removeItem(ACCOUNTS_KEY)
      }

      await initializeAccountAndHideLoading()
      toast.success('已清除本地数据')
    } catch (e) {
      logger.error('App', 'Failed to clear local data', e as Record<string, unknown>)
      toast.error('清除数据失败')
      await initializeAccountAndHideLoading()
    }
  }
}

onMounted(async () => {
  const isSynced = await checkDataSync()

  if (isSynced) {
    await initializeAccountAndHideLoading()
  } else {
    dataSyncDialogRef.value?.open()
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
