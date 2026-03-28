<template>
  <div class="account-settings-content">
    <div class="account-info-section">
      <div class="info-item">
        <label class="info-label">账号名称</label>
        <div class="info-value">{{ currentAccount?.displayName || '-' }}</div>
      </div>

      <div class="info-item">
        <label class="info-label">唯一用户ID</label>
        <div class="info-value-with-action">
          <div class="info-value">{{ currentAccount?.id || '-' }}</div>
          <button
            v-if="currentAccount?.id"
            class="copy-btn"
            type="button"
            title="复制用户ID"
            @click="handleCopyAccountId"
          >
            <IconCopy class="copy-icon" :stroke-width="1.8" style="width: 14px; height: 14px" />
          </button>
        </div>
      </div>

      <div class="info-item">
        <label class="info-label">账号创建时间</label>
        <div class="info-value">{{ formatDate(currentAccount?.createdAt) }}</div>
      </div>
    </div>

    <!-- 退出登录按钮 -->
    <div class="logout-section">
      <button class="logout-btn" type="button" @click="handleLogout">
        <IconLogout class="logout-icon" />
        <span>退出登录</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAccountStore, useAuthStore } from '@/stores'
import { IconCopy } from '@/components/icons'
import { IconLogout } from '@/components/icons'
import { useToast } from '@/composables/useToast'
import { useConfirmDialog } from '@/composables/useModal'
import { logger } from '@/utils/logger'

const accountStore = useAccountStore()
const authStore = useAuthStore()
const router = useRouter()
const toast = useToast()
const confirmDialog = useConfirmDialog()

const currentAccount = computed(() => accountStore.currentAccount)

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

async function handleCopyAccountId(): Promise<void> {
  if (!currentAccount.value?.id) {
    toast.warning('用户ID不存在')
    return
  }

  try {
    await navigator.clipboard.writeText(currentAccount.value.id)
    toast.success('用户ID已复制')
    logger.info('AccountSettings', 'Account ID copied')
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '复制失败'
    toast.error(`复制失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to copy account ID', error)
  }
}

function handleLogout(): void {
  confirmDialog.showDialog('退出登录', '确定要退出登录吗？', 'warning', true, () => {
    // 执行退出操作
    authStore.logout()
    // 重置账号状态
    accountStore.accounts = []
    accountStore.currentAccount = null
    accountStore.currentConfig = null
    accountStore.isInitialized = false
    toast.success('已退出登录')
    logger.info('AccountSettings', 'User logged out')
    // 跳转至登录页面
    router.push('/login')
  })
}
</script>

<style lang="scss" scoped>
.account-settings-content {
  height: 100%;
  overflow-y: auto;
  padding: 0;
}

.account-info-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.info-label {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--text-secondary);
}

.info-value {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  padding: var(--spacing-sm) 0;
}

.info-value-with-action {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  gap: 4px;
}

.info-value-with-action .info-value {
  padding: 0;
}

.copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-tertiary);
  opacity: 0.6;
  transition: all 0.2s ease;

  &:hover {
    opacity: 1;
    color: var(--text-primary);
    background: var(--bg-hover);
  }

  &:active {
    transform: scale(0.9);
  }
}

.copy-icon {
  width: 14px;
  height: 14px;
  display: block;
}

// 退出登录区域样式
.logout-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 24px;
  border: 1px solid #ef4444;
  border-radius: 8px;
  background: #ffffff;
  color: #ef4444;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #ef4444;
    color: #ffffff;
  }

  &:active {
    transform: scale(0.98);
  }
}

.logout-icon {
  width: 18px;
  height: 18px;
}
</style>
