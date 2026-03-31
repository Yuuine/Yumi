<template>
  <div class="account-settings-content">
    <div class="account-info-section">
      <!-- 头像部分 -->
      <div class="avatar-section">
        <div class="avatar-container">
          <img :src="currentAvatarPath" alt="用户头像" class="avatar-image" />
          <button v-if="!isEditing" class="avatar-edit-btn" @click="isEditing = true">
            <IconEdit class="edit-icon" />
          </button>
        </div>
        <div class="avatar-selector" v-if="isEditing">
          <div class="avatar-grid">
            <div
              v-for="avatar in avatarList"
              :key="avatar.id"
              class="avatar-option"
              :class="{ active: selectedAvatarId === avatar.id }"
              @click="selectedAvatarId = avatar.id"
            >
              <img :src="avatar.path" :alt="avatar.name" class="avatar-option-image" />
            </div>
          </div>
        </div>
      </div>

      <!-- 账号信息部分 -->
      <div class="info-item">
        <label class="info-label">账号名称</label>
        <div class="info-value-edit">
          <input
            v-if="isEditing"
            v-model="editRoleName"
            type="text"
            class="edit-input"
            placeholder="请输入账号名称"
            maxlength="20"
          />
          <div v-else class="info-value">{{ currentAccount?.displayName || '-' }}</div>
        </div>
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

    <!-- 编辑操作按钮 -->
    <div class="edit-actions" v-if="isEditing">
      <button class="cancel-btn" type="button" @click="handleCancelEdit" :disabled="isSaving">
        取消
      </button>
      <button class="save-btn" type="button" @click="handleSave" :disabled="isSaving">
        <span v-if="isSaving">保存中...</span>
        <span v-else>保存</span>
      </button>
    </div>

    <!-- 编辑按钮 -->
    <div class="edit-section" v-if="!isEditing">
      <button class="edit-btn" type="button" @click="isEditing = true">
        <IconEdit class="edit-icon" />
        <span>编辑个人信息</span>
      </button>
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
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAccountStore, useAuthStore } from '@/stores'
import { IconCopy } from '@/components/icons'
import { IconLogout } from '@/components/icons'
import { IconEdit } from '@/components/icons'
import { useToast } from '@/composables/useToast'
import { useConfirmDialog } from '@/composables/useModal'
import { logger } from '@/utils/logger'
import { userApi } from '@/api/user'
import { getAvatarPath, AVATARS } from '@/utils/avatar-manager'

const accountStore = useAccountStore()
const authStore = useAuthStore()
const router = useRouter()
const toast = useToast()
const confirmDialog = useConfirmDialog()

// 响应式状态
const isEditing = ref(false)
const isSaving = ref(false)
const editRoleName = ref('')
const selectedAvatarId = ref('avatar1')
const avatarList = AVATARS

const currentAccount = computed(() => accountStore.currentAccount)

// 计算属性
const currentAvatarPath = computed(() => {
  const avatarId = localStorage.getItem(`avatar_${currentAccount.value?.id}`) || 'avatar1'
  return getAvatarPath(avatarId)
})

// 监听账号变化，更新编辑状态
watch(
  currentAccount,
  newAccount => {
    if (newAccount) {
      editRoleName.value = newAccount.displayName || ''
      const savedAvatar = localStorage.getItem(`avatar_${newAccount.id}`)
      if (savedAvatar) {
        selectedAvatarId.value = savedAvatar
      }
    }
  },
  { immediate: true }
)

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

function handleCancelEdit(): void {
  isEditing.value = false
  // 重置表单数据
  if (currentAccount.value) {
    editRoleName.value = currentAccount.value.displayName || ''
    const savedAvatar = localStorage.getItem(`avatar_${currentAccount.value.id}`)
    if (savedAvatar) {
      selectedAvatarId.value = savedAvatar
    }
  }
}

async function handleSave(): Promise<void> {
  if (!currentAccount.value) {
    toast.error('账号信息不存在')
    return
  }

  if (!editRoleName.value.trim()) {
    toast.warning('账号名称不能为空')
    return
  }

  isSaving.value = true

  try {
    // 更新账号名称
    const updatedProfile = await userApi.updateProfile({
      id: currentAccount.value.id,
      roleName: editRoleName.value.trim(),
      preferences: {
        communicationStyle: 'friendly',
        topicsOfInterest: [],
        emotionalSupportLevel: 'medium',
        responseLength: 'medium',
      },
    })

    // 保存头像选择
    localStorage.setItem(`avatar_${currentAccount.value.id}`, selectedAvatarId.value)

    // 更新本地状态
    if (accountStore.currentAccount) {
      accountStore.currentAccount.displayName = updatedProfile.roleName
    }

    isEditing.value = false
    toast.success('个人信息更新成功')
    logger.info('AccountSettings', 'Profile updated successfully')
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : '更新失败'
    toast.error(`更新失败: ${errMsg}`)
    logger.error('AccountSettings', 'Failed to update profile', error)
  } finally {
    isSaving.value = false
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

// 头像部分样式
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.avatar-container {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #e5e7eb;
  transition: all 0.2s ease;

  &:hover {
    border-color: #3b82f6;
  }
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-edit-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #3b82f6;
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;

  &:hover {
    background: #2563eb;
    transform: scale(1.1);
  }
}

.avatar-selector {
  width: 100%;
  margin-top: var(--spacing-sm);
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.avatar-option {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #3b82f6;
    transform: scale(1.05);
  }

  &.active {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
  }
}

.avatar-option-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
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

.info-value-edit {
  position: relative;
}

.edit-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: var(--font-size-sm);
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
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

.edit-icon {
  width: 16px;
  height: 16px;
}

// 编辑操作按钮
.edit-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid #e5e7eb;
}

.cancel-btn {
  flex: 1;
  padding: 10px 20px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #ffffff;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #f3f4f6;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.save-btn {
  flex: 1;
  padding: 10px 20px;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  background: #3b82f6;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #2563eb;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// 编辑按钮
.edit-section {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid #e5e7eb;
}

.edit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 20px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #ffffff;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #f3f4f6;
    border-color: #3b82f6;
  }
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
