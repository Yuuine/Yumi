<template>
  <div class="account-settings-content">
    <div class="account-form">
      <div class="form-section">
        <div class="form-group">
          <label class="form-label">显示名称</label>
          <input
            v-model="displayName"
            type="text"
            class="form-input"
            placeholder="输入账号显示名称"
            @blur="handleUpdateDisplayName"
          />
        </div>

        <div class="form-group">
          <label class="form-label">账号ID</label>
          <div class="form-value-with-action">
            <div class="form-value">{{ currentAccount?.id || '-' }}</div>
            <button
              v-if="currentAccount?.id"
              class="id-copy-btn"
              type="button"
              title="复制账号ID"
              @click="handleCopyAccountId"
            >
              <IconCopy
                class="id-copy-icon"
                :stroke-width="1.8"
                style="width: 14px; height: 14px"
              />
            </button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">创建时间</label>
          <div class="form-value">{{ formatDate(currentAccount?.createdAt) }}</div>
        </div>
      </div>

      <div class="form-section">
        <div class="section-title">数据概览</div>

        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-value">{{ stats.characterCount }}</span>
            <span class="stat-label">角色卡</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.conversationCount }}</span>
            <span class="stat-label">对话</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatSize(stats.dataSize) }}</span>
            <span class="stat-label">存储大小</span>
          </div>
        </div>
      </div>

      <div class="form-section">
        <div class="section-title">安全设置</div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">API密钥加密存储</div>
            <div class="setting-description">开启后，模型账密将被加密存储</div>
          </div>
          <div class="setting-control">
            <ToggleSwitch
              :model-value="encryptEnabled"
              :disabled="isTogglingEncrypt"
              @change="handleToggleEncrypt"
            />
          </div>
        </div>

        <div class="setting-item clickable" @click="showPasswordModal = true">
          <div class="setting-info">
            <div class="setting-label">数据密码</div>
            <div class="setting-description">设置密码后，导出的账号数据将被加密保护</div>
          </div>
          <span class="setting-status" :class="{ active: hasExportPassword }">
            {{ hasExportPassword ? '已设置' : '未设置' }}
          </span>
        </div>
      </div>

      <div class="form-section">
        <div class="section-title">账号相关</div>
        <div class="action-buttons">
          <button class="action-btn" @click="handleExport">
            <IconExport class="btn-icon" />
            <span>导出账号</span>
          </button>
          <button class="action-btn" @click="handleImport">
            <IconExport class="btn-icon import-icon" />
            <span>导入账号</span>
          </button>
        </div>
        <div class="action-buttons account-manage-buttons">
          <button class="action-btn" @click="handleCreateAccount">创建账号</button>
          <button class="action-btn" @click="handleSwitchAccount">切换账号</button>
        </div>
        <button class="action-btn" :disabled="isSyncing" @click="handleSyncAccounts">
          <span v-if="isSyncing" class="btn-loading-spinner"></span>
          <span>{{ isSyncing ? '同步中...' : '发现并同步账号' }}</span>
        </button>
        <button class="action-btn danger full-width" @click="handleDelete">
          <IconDelete class="btn-icon" />
          <span>删除账号</span>
        </button>
      </div>
    </div>

    <Dialog v-model="showPasswordModal" title="设置数据密码">
      <div class="dialog-form">
        <input
          v-model="exportPasswordInput"
          type="password"
          class="form-input"
          placeholder="输入密码（可选）"
        />
        <p class="dialog-hint">留空则清除已设置的密码</p>
      </div>
      <template #footer>
        <button class="dialog-btn" @click="showPasswordModal = false">取消</button>
        <button class="dialog-btn primary" :disabled="isSettingPassword" @click="handleSetPassword">
          {{ isSettingPassword ? '处理中...' : '确定' }}
        </button>
      </template>
    </Dialog>

    <Dialog v-model="showImportModal" title="导入账号">
      <div class="dialog-form">
        <input
          ref="fileInputRef"
          type="file"
          accept=".yumi,.json"
          class="file-input"
          @change="handleFileSelect"
        />
        <input
          v-model="importPassword"
          type="password"
          class="form-input"
          placeholder="请输入数据密码（如无可留空）"
        />
        <p class="dialog-hint">
          {{
            selectedFile ? `已选择: ${selectedFile.name}` : '请选择导出的备份文件（.yumi 或 .json）'
          }}
        </p>
      </div>
      <template #footer>
        <button class="dialog-btn" @click="showImportModal = false">取消</button>
        <button
          class="dialog-btn primary"
          :disabled="!selectedFile || isImporting"
          @click="confirmImport"
        >
          {{ isImporting ? '导入中...' : '导入' }}
        </button>
      </template>
    </Dialog>

    <Dialog v-model="showDeleteConfirm" title="删除账号">
      <div class="dialog-form">
        <p class="dialog-text">请输入“确认”以继续删除账号「{{ currentAccount?.displayName }}」</p>
        <input
          v-model="deleteConfirmText"
          type="text"
          class="form-input"
          placeholder="请输入“确认”"
        />
        <p class="dialog-warning">此操作不可恢复，所有角色卡和对话记录将被永久删除。</p>
      </div>
      <template #footer>
        <button class="dialog-btn" @click="showDeleteConfirm = false">取消</button>
        <button
          class="dialog-btn danger"
          :disabled="!canProceedDeleteStepOne"
          @click="proceedDeleteStepTwo"
        >
          下一步
        </button>
      </template>
    </Dialog>

    <Dialog v-model="showDeleteFinalConfirm" title="最终确认删除">
      <div class="dialog-form">
        <p class="dialog-text">是否确认删除账号？此操作不可恢复</p>
      </div>
      <template #footer>
        <button class="dialog-btn" @click="showDeleteFinalConfirm = false">取消</button>
        <button class="dialog-btn danger" :disabled="!canConfirmDeleteFinal" @click="confirmDelete">
          {{ deleteCountdown > 0 ? `${deleteCountdown}s` : isDeleting ? '删除中...' : '确认删除' }}
        </button>
      </template>
    </Dialog>

    <Dialog v-model="showSwitchAccountModal" title="切换账号">
      <div class="dialog-form">
        <div v-if="accounts.length === 0" class="dialog-hint">未找到本地账号</div>
        <div v-else class="switch-account-list">
          <button
            v-for="account in accounts"
            :key="account.id"
            class="switch-account-item"
            :class="{ active: account.id === currentAccount?.id }"
            @click="confirmSwitchAccount(account.id)"
          >
            <span>{{ account.displayName }}</span>
            <small>{{ account.id }}</small>
          </button>
        </div>
      </div>
      <template #footer>
        <button class="dialog-btn" @click="showSwitchAccountModal = false">关闭</button>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useAccountStore, useChatStore, useModelsStore } from '@/stores'
import { IconExport, IconDelete, IconCopy } from '@/components/icons'
import Dialog from '@/components/common/Dialog.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { useToast } from '@/composables/useToast'
import { logger } from '@/utils/logger'
import { userApi } from '@/api/user'

const DEFAULT_ACCOUNT_CREATED_TOAST_KEY = 'yumi_show_default_account_created_toast'

const accountStore = useAccountStore()
const chatStore = useChatStore()
const modelsStore = useModelsStore()
const toast = useToast()

const displayName = ref('')
const showPasswordModal = ref(false)
const showDeleteConfirm = ref(false)
const showDeleteFinalConfirm = ref(false)
const showImportModal = ref(false)
const showSwitchAccountModal = ref(false)
const savedExportPassword = ref('')
const exportPasswordInput = ref('')
const importPassword = ref('')
const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const hasExportPassword = ref(false)
const isTogglingEncrypt = ref(false)
const isSettingPassword = ref(false)
const isExporting = ref(false)
const isDeleting = ref(false)
const isImporting = ref(false)
const isSyncing = ref(false)
const deleteConfirmText = ref('')
const deleteCountdown = ref(0)
let deleteCountdownTimer: ReturnType<typeof setInterval> | null = null
let statsRefreshTimer: ReturnType<typeof setInterval> | null = null

const stats = ref({
  characterCount: 0,
  conversationCount: 0,
  dataSize: 0,
})

const currentAccount = computed(() => accountStore.currentAccount)
const accounts = computed(() => accountStore.accounts)
const encryptEnabled = computed(() => accountStore.currentConfig?.privacy?.encryptSecrets ?? true)
const canProceedDeleteStepOne = computed(() => deleteConfirmText.value.trim() === '确认')
const canConfirmDeleteFinal = computed(() => deleteCountdown.value === 0 && !isDeleting.value)

watch(
  () => currentAccount.value,
  account => {
    if (account) {
      displayName.value = account.displayName
      logger.debug('AccountSettings', 'Account loaded', {
        id: account.id,
        displayName: account.displayName,
      })
    }
  },
  { immediate: true }
)

onMounted(() => {
  logger.info('AccountSettings', 'Component mounted')
  statsRefreshTimer = setInterval(() => {
    void loadStats()
  }, 3000)
  window.addEventListener('focus', handleWindowFocus)
  void refreshAccountFromBackend()
})

onUnmounted(() => {
  if (statsRefreshTimer) {
    clearInterval(statsRefreshTimer)
    statsRefreshTimer = null
  }
  window.removeEventListener('focus', handleWindowFocus)
})

watch(
  () => accountStore.isInitialized,
  async initialized => {
    if (initialized) {
      await loadStats()
      logger.debug('AccountSettings', 'Stats loaded after initialization', stats.value)
    }
  },
  { immediate: true }
)

watch(
  () => accountStore.currentAccountId,
  () => {
    void loadStats()
  }
)

function handleWindowFocus(): void {
  void loadStats()
  void refreshAccountFromBackend()
}

async function refreshAccountFromBackend() {
  try {
    await accountStore.refreshCurrentAccountFromBackend?.()
  } catch (error) {
    logger.error('AccountSettings', 'Failed to refresh account from backend', error)
  }
}

async function loadStats() {
  try {
    stats.value = await accountStore.getAccountStats()
    logger.debug('AccountSettings', 'Stats loaded', stats.value)
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '加载统计信息失败'
    toast.error(`加载失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to load stats', error)
  }
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

async function handleUpdateDisplayName() {
  if (!displayName.value.trim() || !currentAccount.value) return
  if (displayName.value === currentAccount.value.displayName) return

  logger.debug('AccountSettings', 'Updating display name', { newName: displayName.value })
  try {
    await accountStore.updateAccountProfile({
      displayName: displayName.value.trim(),
    })
    toast.success('显示名称已更新')
    logger.info('AccountSettings', 'Display name updated', { displayName: displayName.value })
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '更新失败'
    toast.error(`更新失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to update display name', error)
  }
}

async function handleCopyAccountId(): Promise<void> {
  if (!currentAccount.value?.id) {
    toast.warning('账号ID不存在')
    return
  }

  try {
    await navigator.clipboard.writeText(currentAccount.value.id)
    toast.success('账号ID已复制')
    logger.info('AccountSettings', 'Account ID copied')
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '复制失败'
    toast.error(`复制失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to copy account ID', error)
  }
}

async function handleToggleEncrypt(): Promise<void> {
  if (!accountStore.currentConfig) {
    logger.warn('AccountSettings', 'Cannot toggle encrypt: no config')
    toast.warning('无法修改加密设置')
    return
  }

  const newValue = !encryptEnabled.value
  logger.debug('AccountSettings', 'Toggling encrypt', { newValue })
  isTogglingEncrypt.value = true
  try {
    await accountStore.updateAccountConfig({
      privacy: {
        ...accountStore.currentConfig.privacy,
        encryptSecrets: newValue,
      },
    })
    toast.success(newValue ? '已启用API密钥加密存储' : '已关闭API密钥加密存储')
    logger.info('AccountSettings', 'Encrypt toggled', { encryptSecrets: newValue })
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '操作失败'
    toast.error(`操作失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to toggle encrypt', error)
  } finally {
    isTogglingEncrypt.value = false
  }
}

async function handleSetPassword(): Promise<void> {
  isSettingPassword.value = true
  try {
    savedExportPassword.value = exportPasswordInput.value
    hasExportPassword.value = exportPasswordInput.value.length > 0
    logger.info('AccountSettings', 'Data password set', { hasPassword: hasExportPassword.value })
    showPasswordModal.value = false
    toast.success(hasExportPassword.value ? '数据密码已设置' : '数据密码已清除')
    exportPasswordInput.value = ''
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '设置数据密码失败'
    toast.error(`设置失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to set export password', error)
  } finally {
    isSettingPassword.value = false
  }
}

function handleExport() {
  void exportNow()
}

function handleImport() {
  selectedFile.value = null
  importPassword.value = ''
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  showImportModal.value = true
}

async function handleCreateAccount(): Promise<void> {
  try {
    const created = await accountStore.createDefaultAccount()
    const accountSuffix = created.id.slice(-6)
    toast.success(`已创建并切换到新账号：${created.displayName}（...${accountSuffix}）`)
    logger.info('AccountSettings', 'Default account created from settings', {
      accountId: created.id,
    })
    await loadStats()
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '创建账号失败'
    toast.error(`创建失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to create account from settings', error)
  }
}

function handleSwitchAccount(): void {
  showSwitchAccountModal.value = true
}

async function confirmSwitchAccount(accountId: string): Promise<void> {
  try {
    await accountStore.switchAccount(accountId)
    showSwitchAccountModal.value = false
    toast.success('账号切换成功')
    logger.info('AccountSettings', 'Account switched from settings', { accountId })
    await loadStats()
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '切换账号失败'
    toast.error(`切换失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to switch account from settings', error)
  }
}

async function handleSyncAccounts(): Promise<void> {
  isSyncing.value = true
  try {
    const result = await accountStore.syncAccountsFromBackend()
    if (result.imported > 0) {
      toast.success(`成功发现并导入 ${result.imported} 个账号`)
    } else if (result.alreadyExisted > 0) {
      toast.info(`没有发现新账号，已有 ${result.alreadyExisted} 个账号在本地`)
    } else {
      toast.info('没有发现任何账号')
    }
    logger.info('AccountSettings', 'Accounts synced successfully', result)
    await loadStats()
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '同步账号失败'
    toast.error(`同步失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to sync accounts', error)
  } finally {
    isSyncing.value = false
  }
}

function handleFileSelect(event: Event): void {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files && input.files.length > 0 ? input.files[0] : null
}

async function exportNow() {
  if (isExporting.value) return
  logger.debug('AccountSettings', 'Exporting account directly')
  isExporting.value = true
  try {
    const password = savedExportPassword.value || undefined
    const blob = await accountStore.exportAccount(password)

    const timestamp = new Date().toISOString().slice(0, 10)
    const filename = `yumi_backup_${currentAccount.value?.displayName || 'account'}_${timestamp}.yumi`

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast.success('账号导出成功')
    logger.info('AccountSettings', 'Account exported', { filename, hasPassword: !!password })
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '导出失败'
    toast.error(`导出失败: ${errMsg}`)
    logger.error('AccountSettings', 'Export failed', error)
  } finally {
    isExporting.value = false
  }
}

function handleDelete() {
  logger.debug('AccountSettings', 'Delete button clicked')
  deleteConfirmText.value = ''
  showDeleteFinalConfirm.value = false
  showDeleteConfirm.value = true
}

function proceedDeleteStepTwo(): void {
  if (!canProceedDeleteStepOne.value) {
    toast.warning('请输入“确认”以继续')
    return
  }
  showDeleteConfirm.value = false
  showDeleteFinalConfirm.value = true
  startDeleteCountdown()
}

function startDeleteCountdown(): void {
  if (deleteCountdownTimer) {
    clearInterval(deleteCountdownTimer)
  }
  deleteCountdown.value = 3
  deleteCountdownTimer = setInterval(() => {
    if (deleteCountdown.value <= 1) {
      deleteCountdown.value = 0
      if (deleteCountdownTimer) {
        clearInterval(deleteCountdownTimer)
        deleteCountdownTimer = null
      }
      return
    }
    deleteCountdown.value -= 1
  }, 1000)
}

function wait(ms: number): Promise<void> {
  return new Promise(resolve => {
    setTimeout(resolve, ms)
  })
}

async function confirmDelete() {
  if (isDeleting.value) return
  if (!currentAccount.value) {
    logger.warn('AccountSettings', 'Cannot delete: no current account')
    toast.warning('无法删除：账号不存在')
    return
  }

  logger.debug('AccountSettings', 'Confirming delete', { accountId: currentAccount.value.id })
  isDeleting.value = true
  try {
    const deletedId = currentAccount.value.id
    await userApi.purgeUserData(deletedId)
    await accountStore.deleteAccount(deletedId)

    chatStore.clearMessages()

    if (accountStore.currentAccountId) {
      chatStore.currentUserId = accountStore.currentAccountId
      await Promise.all([
        chatStore.loadHistory(),
        modelsStore.loadModels(),
        modelsStore.loadActiveModel(),
      ])
    }

    showDeleteConfirm.value = false

    if (!accountStore.hasAccounts) {
      logger.info(
        'AccountSettings',
        'No accounts remaining, reloading app for fresh initialization'
      )
      toast.success('账号已彻底删除，正在清理并重置...')
      sessionStorage.setItem(DEFAULT_ACCOUNT_CREATED_TOAST_KEY, '1')
      await wait(3000)
      window.location.reload()
      return
    }

    showDeleteFinalConfirm.value = false
    const switchedAccount = accountStore.currentAccount
    if (switchedAccount) {
      toast.success(`账号已删除，已自动切换到：${switchedAccount.displayName}`)
    } else {
      toast.success('账号已删除，关联历史记录与模型配置已清理')
    }
    logger.info('AccountSettings', 'Account deleted', { accountId: deletedId })
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '删除失败'
    toast.error(`删除失败: ${errMsg}`)
    logger.error('AccountSettings', 'Delete failed', error)
  } finally {
    isDeleting.value = false
    if (deleteCountdownTimer) {
      clearInterval(deleteCountdownTimer)
      deleteCountdownTimer = null
    }
    deleteCountdown.value = 0
  }
}

async function confirmImport(): Promise<void> {
  if (!selectedFile.value || isImporting.value) return

  isImporting.value = true
  try {
    const text = await selectedFile.value.text()
    const parsed = JSON.parse(text) as { secrets?: { encryptedBackup?: unknown } }
    const password = importPassword.value.trim() || undefined

    if (parsed.secrets?.encryptedBackup && !password) {
      toast.error('导入失败，请输入密码')
      return
    }

    const imported = await accountStore.importAccount(selectedFile.value, password)
    await accountStore.switchAccount(imported.id)
    await loadStats()

    showImportModal.value = false
    selectedFile.value = null
    importPassword.value = ''
    toast.success('账号导入成功，已切换到新账号')
    logger.info('AccountSettings', 'Account imported from settings', { accountId: imported.id })
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '导入失败'
    if (errMsg.includes('密码错误') || errMsg.includes('Invalid password')) {
      toast.error('密码错误')
    } else {
      toast.error(`导入失败: ${errMsg}`)
    }
    logger.error('AccountSettings', 'Import failed in settings', error)
  } finally {
    isImporting.value = false
  }
}
</script>

<style lang="scss" scoped>
.account-settings-content {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  scrollbar-gutter: stable;
}

.account-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-section {
  .section-title {
    font-size: var(--font-size-sm);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--border-color-lighter);
  }
}

.form-group {
  margin-bottom: var(--spacing-md);

  &:last-child {
    margin-bottom: 0;
  }
}

.form-label {
  display: block;
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.form-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color var(--transition-fast);

  &:focus {
    outline: none;
    border-color: var(--color-primary);
  }

  &::placeholder {
    color: var(--text-placeholder);
  }
}

.form-value {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  padding: var(--spacing-sm) 0;
}

.form-value-with-action {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  gap: 4px;
}

.form-value-with-action .form-value {
  padding: 0;
}

.id-copy-btn {
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

.id-copy-icon {
  width: 14px;
  height: 14px;
  display: block;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);

  .stat-value {
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
  }

  .stat-label {
    font-size: var(--font-size-xs);
    color: var(--text-secondary);
  }
}

.action-buttons {
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    background: var(--bg-hover);
    border-color: var(--border-color);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &.danger {
    color: var(--color-danger);
    background: var(--color-danger-light-9);
    border-color: var(--color-danger-light-7);

    &:hover {
      background: var(--color-danger-light-7);
      border-color: var(--color-danger-light-5);
    }
  }

  .btn-icon {
    width: 18px;
    height: 18px;
  }

  .import-icon {
    transform: rotate(180deg);
  }
}

.action-btn.full-width {
  flex: 0 0 auto;
  width: 100%;
  max-width: 320px;
  margin: var(--spacing-md) auto 0;
}

.account-manage-buttons {
  margin-top: var(--spacing-sm);
}

.btn-loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(48, 49, 51, 0.3);
  border-top-color: var(--text-primary, #303133);
  border-radius: 50%;
  animation: btn-spin 0.8s linear infinite;
}

@keyframes btn-spin {
  to {
    transform: rotate(360deg);
  }
}

.switch-account-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.switch-account-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  cursor: pointer;
  color: var(--text-primary);

  &.active {
    border-color: var(--color-primary);
    background: var(--color-primary-light-9, #eff6ff);
  }

  small {
    font-size: var(--font-size-xs);
    color: var(--text-secondary);
  }
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-sm);

  &:last-child {
    margin-bottom: 0;
  }

  &.clickable {
    cursor: pointer;

    &:hover {
      background: var(--bg-hover);
      border-color: var(--border-color);
    }
  }
}

.setting-info {
  flex: 1;
  min-width: 0;
}

.setting-label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.setting-description {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  line-height: 1.5;
}

.setting-control {
  margin-left: var(--spacing-md);
  flex-shrink: 0;
}

.setting-status {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  flex-shrink: 0;

  &.active {
    color: var(--color-success);
  }
}

.dialog-form {
  padding: var(--spacing-md) 0;

  .form-input {
    width: 100%;
  }

  .dialog-hint {
    margin-top: var(--spacing-sm);
    font-size: var(--font-size-xs);
    color: var(--text-secondary);
  }

  .dialog-text {
    margin: 0 0 var(--spacing-sm) 0;
    font-size: var(--font-size-sm);
    color: var(--text-primary);
  }

  .dialog-warning {
    color: var(--color-danger);
    font-size: var(--font-size-xs);
  }

  .file-input {
    width: 100%;
    margin-bottom: var(--spacing-sm);
  }
}

.dialog-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);

  &:hover {
    background: var(--bg-hover);
  }

  &.primary {
    background: var(--color-primary);
    color: #ffffff;
    border-color: var(--color-primary);

    &:hover {
      background: var(--color-primary-dark-2);
    }
  }

  &.danger {
    background: var(--color-danger);
    color: #ffffff;
    border-color: var(--color-danger);

    &:hover {
      background: #dc2626;
    }
  }
}
</style>
