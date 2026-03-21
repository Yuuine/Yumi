<template>
  <Teleport to="body">
    <template v-if="visible">
      <Transition name="modal">
        <div class="selector-overlay">
          <div class="selector-modal">
            <div class="modal-header">
              <h2 class="modal-title">选择账号</h2>
            </div>

            <div class="modal-body">
              <div class="account-list">
                <div
                  v-for="account in accounts"
                  :key="account.id"
                  class="account-item"
                  :class="{ active: account.id === currentAccount?.id }"
                  @click="handleSelectAccount(account.id)"
                >
                  <div class="account-info">
                    <div class="account-name">{{ account.displayName }}</div>
                    <div class="account-meta">
                      <span>上次使用: {{ formatLastActive(account.lastActiveAt) }}</span>
                    </div>
                  </div>
                  <div v-if="account.id === currentAccount?.id" class="active-indicator">
                    <IconCheck class="check-icon" />
                  </div>
                </div>
              </div>

              <div class="action-bar">
                <button class="action-btn" @click="handleCreateAccount">
                  <IconAdd class="btn-icon" />
                  <span>新建账号</span>
                </button>
                <button class="action-btn" @click="handleImportAccount">
                  <IconImport class="btn-icon" />
                  <span>导入账号</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <Dialog :visible="showImportDialog" title="导入账号" @close="showImportDialog = false">
        <div class="import-form">
          <input ref="fileInput" type="file" accept=".yumi,.json" @change="handleFileSelect" />
          <p class="import-hint">选择之前导出的账号备份文件</p>

          <input
            v-if="selectedFile"
            v-model="importPassword"
            type="password"
            class="form-input"
            placeholder="如果备份有密码，请输入密码"
          />
        </div>
        <template #footer>
          <button class="dialog-btn" @click="showImportDialog = false">取消</button>
          <button class="dialog-btn primary" :disabled="!selectedFile" @click="confirmImport">
            导入
          </button>
        </template>
      </Dialog>
    </template>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAccountStore } from '@/stores'
import { IconAdd, IconCheck } from '@/components/icons'
import Dialog from '@/components/common/Dialog.vue'
import { logger } from '@/utils/logger'

const IconImport = {
  template: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
}

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  createNew: []
}>()

const accountStore = useAccountStore()

const showImportDialog = ref(false)
const selectedFile = ref<File | null>(null)
const importPassword = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const accounts = computed(() => accountStore.accounts)
const currentAccount = computed(() => accountStore.currentAccount)

function formatLastActive(dateStr?: string): string {
  if (!dateStr) return '从未'

  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  if (days < 30) return `${Math.floor(days / 7)}周前`
  return date.toLocaleDateString('zh-CN')
}

async function handleSelectAccount(accountId: string) {
  if (accountId === currentAccount.value?.id) {
    emit('close')
    return
  }

  try {
    await accountStore.switchAccount(accountId)
    emit('close')
    logger.info('AccountSelector', 'Account selected', { accountId })
  } catch (error) {
    logger.error('AccountSelector', 'Failed to select account', error)
  }
}

function handleCreateAccount() {
  emit('createNew')
  emit('close')
}

function handleImportAccount() {
  selectedFile.value = null
  importPassword.value = ''
  showImportDialog.value = true
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
  }
}

async function confirmImport() {
  if (!selectedFile.value) return

  try {
    const password = importPassword.value || undefined
    await accountStore.importAccount(selectedFile.value, password)
    showImportDialog.value = false
    emit('close')
    logger.info('AccountSelector', 'Account imported')
  } catch (error) {
    logger.error('AccountSelector', 'Failed to import account', error)
  }
}
</script>

<style lang="scss" scoped>
.selector-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.selector-modal {
  background: #ffffff;
  border-radius: 12px;
  width: 400px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;

  .modal-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #333333;
    text-align: center;
  }
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f9fafb;
  border: 2px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #f3f4f6;
    border-color: #e5e7eb;
  }

  &.active {
    background: #eff6ff;
    border-color: #3b82f6;
  }
}

.account-info {
  flex: 1;
}

.account-name {
  font-size: 15px;
  font-weight: 600;
  color: #333333;
  margin-bottom: 4px;
}

.account-meta {
  font-size: 12px;
  color: #666666;
}

.active-indicator {
  width: 24px;
  height: 24px;
  background: #3b82f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;

  .check-icon {
    width: 14px;
    height: 14px;
    color: #ffffff;
  }
}

.action-bar {
  display: flex;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid #e5e7eb;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #333333;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
  }

  .btn-icon {
    width: 18px;
    height: 18px;
  }
}

.import-form {
  padding: 16px 0;

  input[type='file'] {
    margin-bottom: 12px;
  }

  .import-hint {
    margin: 0 0 12px 0;
    font-size: 12px;
    color: #666666;
  }

  .form-input {
    width: 100%;
    padding: 10px 12px;
    font-size: 14px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;

    &:focus {
      outline: none;
      border-color: #3b82f6;
    }
  }
}

.dialog-btn {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;

  &.primary {
    background: #3b82f6;
    color: #ffffff;
    border: none;

    &:hover:not(:disabled) {
      background: #2563eb;
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;

  .selector-modal {
    transition:
      transform 0.25s ease,
      opacity 0.25s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .selector-modal {
    transform: scale(0.95) translateY(-20px);
    opacity: 0;
  }
}
</style>
