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
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAccountStore } from '@/stores'
import { IconCopy } from '@/components/icons'
import { useToast } from '@/composables/useToast'
import { logger } from '@/utils/logger'

const accountStore = useAccountStore()
const toast = useToast()

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
</style>
