<template>
  <div>
    <el-dialog
      v-model="showSyncDialog"
      title="数据同步检测"
      width="600px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="sync-dialog-content">
        <div class="warning-section">
          <el-icon class="warning-icon"><IconWarning /></el-icon>
          <p class="warning-text">检测到后端数据已清空，但本地还有数据。</p>
        </div>
        <div class="options-section">
          <el-radio-group v-model="selectedOption" class="option-group">
            <el-radio label="restart" class="option-item">
              <div class="option-content">
                <div class="option-title">重新开始</div>
                <div class="option-desc">清除本地数据，创建新账号</div>
              </div>
            </el-radio>
            <el-radio label="sync" class="option-item">
              <div class="option-content">
                <div class="option-title">同步到后端</div>
                <div class="option-desc">把本地数据推送到后端数据库</div>
              </div>
            </el-radio>
          </el-radio-group>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" :loading="processing" @click="handleConfirm">
            确认
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showErrorDialog"
      title="数据损坏，同步失败"
      width="550px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="error-dialog-content">
        <div class="error-section">
          <el-icon class="error-icon"><IconError /></el-icon>
          <p class="error-text">检测到数据库数据损坏或不完整，导致同步失败。</p>
        </div>
        <div class="error-options-section">
          <el-radio-group v-model="errorOption" class="option-group">
            <el-radio label="retry" class="option-item">
              <div class="option-content">
                <div class="option-title">继续同步</div>
                <div class="option-desc">再次尝试同步数据到后端</div>
              </div>
            </el-radio>
            <el-radio label="delete" class="option-item error-option">
              <div class="option-content">
                <div class="option-title">删除数据</div>
                <div class="option-desc">清除所有本地数据，重新开始</div>
              </div>
            </el-radio>
          </el-radio-group>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" :loading="errorProcessing" @click="handleErrorConfirm">
            确认
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { IconWarning, IconError } from '@/components/icons'
import { useToast } from '@/composables/useToast'
import { logger } from '@/utils/logger'

const toast = useToast()

const emit = defineEmits<{
  confirm: [option: 'restart' | 'sync']
  errorConfirm: [option: 'retry' | 'delete']
}>()

const showSyncDialog = ref(false)
const showErrorDialog = ref(false)
const processing = ref(false)
const errorProcessing = ref(false)
const selectedOption = ref<'restart' | 'sync'>('restart')
const errorOption = ref<'retry' | 'delete'>('retry')

function open() {
  showSyncDialog.value = true
  selectedOption.value = 'restart'
  processing.value = false
}

function openError() {
  showErrorDialog.value = true
  errorOption.value = 'retry'
  errorProcessing.value = false
}

async function handleConfirm() {
  processing.value = true
  try {
    emit('confirm', selectedOption.value)
    showSyncDialog.value = false
  } catch (e) {
    logger.error('DataSyncDialog', 'Failed to handle confirm', e as Record<string, unknown>)
    toast.error('操作失败，请重试')
  } finally {
    processing.value = false
  }
}

async function handleErrorConfirm() {
  errorProcessing.value = true
  try {
    emit('errorConfirm', errorOption.value)
    showErrorDialog.value = false
  } catch (e) {
    logger.error('DataSyncDialog', 'Failed to handle error confirm', e as Record<string, unknown>)
    toast.error('操作失败，请重试')
  } finally {
    errorProcessing.value = false
  }
}

defineExpose({
  open,
  openError,
})
</script>

<style lang="scss" scoped>
.sync-dialog-content,
.error-dialog-content {
  padding: 12px 0;
}

.warning-section,
.error-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px;
  background: var(--bg-secondary);
  border-radius: 12px;
  margin-bottom: 24px;
}

.warning-icon {
  font-size: 56px;
  color: #f59e0b;
}

.error-icon {
  font-size: 56px;
  color: #ef4444;
}

.warning-text,
.error-text {
  font-size: 15px;
  color: var(--text-primary);
  text-align: center;
  margin: 0;
  line-height: 1.6;
}

.options-section,
.error-options-section {
  padding: 0 12px;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.option-item {
  width: 100%;
  padding: 26px 24px;
  border: 2px solid var(--border-color, #e5e7eb);
  border-radius: 12px;
  margin: 0;
  transition: all 0.2s;

  &:hover {
    border-color: #3b82f6;
    background: rgba(59, 130, 246, 0.05);
  }

  &.error-option:hover {
    border-color: #ef4444;
    background: rgba(239, 68, 68, 0.05);
  }

  :deep(.el-radio__label) {
    width: 100%;
  }
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.option-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0;
}

.option-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
