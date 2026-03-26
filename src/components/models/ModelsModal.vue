<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="models-modal-overlay" @click.self="handleClose">
        <div class="models-modal">
          <div class="modal-header">
            <h2 class="modal-title">模型管理</h2>
            <div class="header-actions">
              <button
                class="add-btn"
                @click="showAddDialog"
                :disabled="isTestingModel"
                type="button"
              >
                <IconAdd class="btn-icon" />
                <span>添加</span>
              </button>
              <button
                class="close-btn"
                @click="handleClose"
                aria-label="关闭"
                :disabled="isTestingModel"
                type="button"
              >
                <IconClose />
              </button>
            </div>
          </div>

          <div class="modal-body">
            <div
              v-if="modelsStore.isLoading && modelsStore.models.length === 0"
              class="loading-state"
            >
              <div class="spinner"></div>
              <span>加载中...</span>
            </div>

            <div v-else-if="modelsStore.models.length === 0" class="empty-state">
              <IconError class="empty-icon" />
              <p>暂无模型配置</p>
            </div>

            <div v-else class="models-list">
              <ModelCard
                v-for="model in modelsStore.models"
                :key="model.id"
                :model="model"
                :is-testing="isTestingModel"
                @test="handleTest(model)"
                @edit="handleEdit(model)"
                @clone="handleClone(model)"
                @toggle="handleToggle(model)"
                @delete="handleDelete(model.id)"
              />
            </div>
          </div>

          <LoadingState v-if="isTestingModel" :text="`正在测试「${testingModelName}」连接...`" />
        </div>
      </div>
    </Transition>

    <Transition name="modal">
      <div v-if="formDialogVisible" class="models-modal-overlay" @click.self="handleCancel">
        <div class="form-dialog">
          <div class="dialog-header">
            <h3>{{ isEditing ? '编辑模型' : '添加模型' }}</h3>
            <button class="close-btn" @click="handleCancel" aria-label="关闭" type="button">
              <IconClose />
            </button>
          </div>

          <div class="dialog-body">
            <ModelForm
              ref="modelFormRef"
              v-model="formData"
              :is-editing="isEditing"
              :original-api-key="originalApiKey"
              @api-key-changed="handleApiKeyChanged"
            />
          </div>

          <div class="dialog-footer">
            <button class="dialog-btn secondary" @click="handleCancel" type="button">取消</button>
            <button
              class="dialog-btn primary"
              @click="handleSubmit"
              :disabled="isSubmitting"
              type="button"
            >
              {{ isSubmitting ? '处理中...' : isEditing ? '保存' : '确定' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>



    <TestResultDialog
      :visible="testDialogVisible"
      :result="modelsStore.testResult"
      @close="testDialogVisible = false"
    />

    <Toast />
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { useModelsStore, useSettingsStore } from '@/stores'
import { useToast, useConfirmDialog } from '@/composables'
import type { ModelConfig } from '@/types'
import { logger } from '@/utils/logger'
import LoadingState from '@/components/common/LoadingState.vue'
import Toast from '@/components/common/Toast.vue'
import ModelCard from './ModelCard.vue'
import ModelForm from './ModelForm.vue'
import TestResultDialog from './TestResultDialog.vue'
import { IconClose, IconError, IconAdd } from '@/components/icons'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const modelsStore = useModelsStore()
const settingsStore = useSettingsStore()
const toast = useToast()
const confirmDialog = useConfirmDialog()

const formDialogVisible = ref(false)
const testDialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const isSubmitting = ref(false)
const isTestingModel = ref(false)
const testingModelName = ref('')
const modelFormRef = ref<InstanceType<typeof ModelForm> | null>(null)

let formData = reactive({
  providerId: 'deepseek',
  name: '',
  baseUrl: 'https://api.deepseek.com',
  apiKey: '',
  modelName: 'deepseek-chat',
})

const originalApiKey = ref('')
const apiKeyChanged = ref(false)

function resetFormData(): void {
  formData.providerId = 'deepseek'
  formData.name = ''
  formData.baseUrl = 'https://api.deepseek.com'
  formData.apiKey = ''
  formData.modelName = 'deepseek-chat'
  originalApiKey.value = ''
  apiKeyChanged.value = false
}

function handleApiKeyChanged(changed: boolean): void {
  apiKeyChanged.value = changed
}

function handleClose(): void {
  emit('close')
}

function handleCancel(): void {
  formDialogVisible.value = false
  resetFormData()
}

function showAddDialog(): void {
  isEditing.value = false
  editingId.value = null
  resetFormData()
  modelFormRef.value?.reset()
  formDialogVisible.value = true
}

function handleEdit(model: ModelConfig): void {
  isEditing.value = true
  editingId.value = model.id
  originalApiKey.value = model.apiKey
  modelFormRef.value?.setFormData(model)
  apiKeyChanged.value = false
  formDialogVisible.value = true
}

async function handleClone(model: ModelConfig): Promise<void> {
  isEditing.value = false
  editingId.value = null
  modelFormRef.value?.setFormData({
    ...model,
    name: `${model.name} Copy`,
  })
  formDialogVisible.value = true
}

async function handleToggle(model: ModelConfig): Promise<void> {
  try {
    if (model.isEnabled) {
      await modelsStore.disableModel(model.id)
      toast.success('模型已禁用')
    } else {
      if (!model.apiKey) {
        confirmDialog.showDialog('无法启用', '请先配置 API 密钥', 'warning')
        return
      }
      const result = await modelsStore.enableModel(model.id)
      if (!result.success) {
        confirmDialog.showDialog('启用失败', result.message, 'error')
        return
      }
      toast.success('模型已启用')
    }
  } catch (error) {
    logger.error('ModelsModal', 'Failed to toggle model', error)
    confirmDialog.showDialog('操作失败', '请稍后重试', 'error')
  }
}

function handleDelete(modelId: string): void {
  confirmDialog.showDialog(
    '确认删除',
    '确定要删除这个模型配置吗？此操作不可撤销。',
    'warning',
    true,
    async () => {
      try {
        await modelsStore.deleteModelSilent(modelId)
        toast.success('模型已删除')
      } catch (error) {
        logger.error('ModelsModal', 'Failed to delete model', error)
        confirmDialog.showDialog('删除失败', '请稍后重试', 'error')
      }
    }
  )
}

async function handleTest(model: ModelConfig): Promise<void> {
  if (!model.apiKey) {
    toast.warning('请先配置 API 密钥')
    return
  }

  isTestingModel.value = true
  testingModelName.value = model.name

  try {
    await modelsStore.testModelById(model.id, settingsStore.verboseTest)
    testDialogVisible.value = true
  } catch (error) {
    logger.error('ModelsModal', 'Failed to test model', error)
    confirmDialog.showDialog('测试失败', '请检查网络连接和 API 配置', 'error')
  } finally {
    isTestingModel.value = false
    testingModelName.value = ''
  }
}

async function handleSubmit(): Promise<void> {
  if (!isEditing.value && !formData.apiKey.trim()) {
    confirmDialog.showDialog('提示', '请输入 API 密钥', 'warning')
    return
  }

  const config: Omit<ModelConfig, 'id'> & { apiKeyUnchanged?: boolean } = {
    providerId: formData.providerId,
    name: formData.name.trim() || '',
    baseUrl: formData.baseUrl,
    apiKey: formData.apiKey,
    modelName: formData.modelName,
    modelType: 'text',
    maxTokens: 4096,
    temperature: 0.85,
    isEnabled: false,
    isTested: false,
    testStatus: 'untested',
    editCount: 0,
  }

  if (isEditing.value && !apiKeyChanged.value) {
    config.apiKeyUnchanged = true
  }

  isSubmitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      await modelsStore.updateModelSilent(editingId.value, config)
      toast.success('模型已更新')
    } else {
      await modelsStore.createModelSilent(config)
      toast.success('模型已添加')
    }
    formDialogVisible.value = false
    resetFormData()
    await modelsStore.loadModels()
  } catch (error) {
    logger.error('ModelsModal', 'Failed to submit model', error)
    confirmDialog.showDialog('操作失败', '请稍后重试', 'error')
  } finally {
    isSubmitting.value = false
  }
}

watch(
  () => props.visible,
  async visible => {
    if (visible) {
      await modelsStore.loadModels()
    }
  }
)

onMounted(async () => {
  if (props.visible) {
    await modelsStore.loadModels()
  }
})
</script>

<style lang="scss" scoped>
.models-modal-overlay {
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

.models-modal {
  position: relative;
  background: #ffffff;
  border-radius: 12px;
  width: 960px;
  max-width: 95vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;

  .modal-title {
    margin: 0;
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: #333333;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #ff9500;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: var(--font-size-xs);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #e68600;
  }

  .btn-icon {
    width: 16px;
    height: 16px;
  }
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #9ca3af;
  transition: all 0.2s;

  &:hover {
    background: #f3f4f6;
    color: #333333;
  }

  svg {
    width: 20px;
    height: 20px;
  }
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px 24px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: #666666;

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid #e5e7eb;
    border-top-color: #ff9500;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 12px;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: #666666;

  .empty-icon {
    width: 48px;
    height: 48px;
    margin-bottom: 16px;
    color: #9ca3af;
  }

  p {
    margin: 0;
    font-size: 14px;
  }
}

.models-list {
  display: flex;
  flex-direction: column;
}

.form-dialog {
  background: #ffffff;
  border-radius: 12px;
  width: 600px;
  max-width: 80vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;

  h3 {
    margin: 0;
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: #333333;
  }
}

.dialog-body {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

.dialog-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: var(--font-size-xs);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &.secondary {
    background: #f3f4f6;
    color: #666666;

    &:hover {
      background: #e5e7eb;
    }
  }

  &.primary {
    background: #3b82f6;
    color: #ffffff;

    &:hover {
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

  .models-modal,
  .form-dialog {
    transition:
      transform 0.25s ease,
      opacity 0.25s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .models-modal,
  .form-dialog {
    transform: scale(0.95) translateY(-20px);
    opacity: 0;
  }
}
</style>
