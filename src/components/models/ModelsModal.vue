<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="models-modal-overlay" @click.self="handleClose">
        <div class="models-modal">
          <div class="modal-header">
            <h2 class="modal-title">模型管理</h2>
            <div class="header-actions">
              <button class="add-btn" @click="showAddDialog" :disabled="isTestingModel">
                <IconAdd class="btn-icon" />
                <span>添加</span>
              </button>
              <button class="close-btn" @click="handleClose" aria-label="关闭" :disabled="isTestingModel">
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
              <div v-for="model in modelsStore.models" :key="model.id" class="model-card">
                <div class="card-left">
                  <div class="model-name">{{ model.name }}</div>
                  <div class="model-tags">
                    <span class="tag tag-provider">{{ providerNames[model.providerId] || model.providerId }}</span>
                    <span class="tag tag-model">{{ model.modelName }}</span>
                    <span v-if="getCapabilities(model.modelName).toolCall" class="tag tag-tool">
                      工具调用
                    </span>
                    <span v-if="getCapabilities(model.modelName).reasoning" class="tag tag-reasoning">
                      推理模式
                    </span>
                    <span v-if="getCapabilities(model.modelName).webSearch" class="tag tag-websearch">
                      联网搜索
                    </span>
                    <span v-if="getCapabilities(model.modelName).multimodal" class="tag tag-multimodal">
                      多模态
                    </span>
                    <span v-if="model.isEnabled" class="tag tag-enabled">已启用</span>
                    <span v-else class="tag tag-disabled">已禁用</span>
                  </div>
                </div>

                <div class="card-right">
                  <button
                    class="action-btn"
                    @click="handleTest(model)"
                    :disabled="modelsStore.isTesting || isTestingModel"
                  >
                    <IconLink :stroke-width="1.5" />
                    <span>测试</span>
                  </button>
                  <button class="action-btn" @click="handleEdit(model)" :disabled="isTestingModel">
                    <IconEdit :stroke-width="1.5" />
                    <span>编辑</span>
                  </button>
                  <button class="action-btn" @click="handleClone(model)" :disabled="isTestingModel">
                    <IconCopy :stroke-width="1.5" />
                    <span>克隆</span>
                  </button>
                  <button
                    class="action-btn"
                    :class="model.isEnabled ? 'disable-btn' : 'enable-btn'"
                    @click="handleToggle(model)"
                    :disabled="isTestingModel"
                  >
                    <IconDisable v-if="model.isEnabled" :stroke-width="1.5" />
                    <IconSuccess v-else :stroke-width="1.5" />
                    <span>{{ model.isEnabled ? '禁用' : '启用' }}</span>
                  </button>
                  <button class="action-btn delete-btn" @click="handleDelete(model.id)" :disabled="isTestingModel">
                    <IconDelete :stroke-width="1.5" />
                    <span>删除</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <LoadingOverlay
            :visible="isTestingModel"
            :text="`正在测试「${testingModelName}」连接...`"
            :show-timeout="true"
            :timeout="60000"
            @timeout="handleTestTimeout"
          />
        </div>
      </div>
    </Transition>

    <Transition name="modal">
      <div
        v-if="formDialogVisible"
        class="models-modal-overlay"
        @click.self="formDialogVisible = false"
      >
        <div class="form-dialog">
          <div class="dialog-header">
            <h3>{{ isEditing ? '编辑模型' : '添加模型' }}</h3>
            <button class="close-btn" @click="formDialogVisible = false" aria-label="关闭">
              <IconClose />
            </button>
          </div>

          <div class="dialog-body">
            <div class="form-section">
              <div class="section-title">提供商配置</div>

              <div class="form-item">
                <label class="form-label">提供商</label>
                <div class="form-control">
                  <select
                    v-model="formData.providerId"
                    class="form-select"
                    @change="handleProviderChange"
                  >
                    <option v-for="opt in providerOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                  <IconChevronDown class="select-arrow" />
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">API 地址</label>
                <input
                  v-model="formData.baseUrl"
                  type="text"
                  class="form-input"
                  placeholder="https://api.openai.com/v1"
                />
              </div>

              <div class="form-item">
                <label class="form-label">API 密钥</label>
                <div class="form-control-wrapper">
                  <input
                    v-model="formData.apiKey"
                    type="password"
                    class="form-input"
                    placeholder="输入 API 密钥"
                  />
                  <button
                    class="icon-btn"
                    title="前往获取 API 密钥"
                    @click="openApiKeyPage"
                    aria-label="获取 API 密钥"
                  >
                    <IconLink :stroke-width="1.5" />
                  </button>
                </div>
              </div>
            </div>

            <div class="form-section">
              <div class="section-title">模型配置</div>

              <div class="form-item">
                <label class="form-label">显示名称</label>
                <input
                  v-model="formData.name"
                  type="text"
                  class="form-input"
                  placeholder="例如: DeepSeek 主力模型"
                />
              </div>

              <div class="form-item">
                <label class="form-label">选择模型</label>
                <div class="form-control">
                  <select v-model="formData.modelName" class="form-select">
                    <option
                      v-for="model in availableModels"
                      :key="model.value"
                      :value="model.value"
                    >
                      {{ model.label }}
                    </option>
                  </select>
                  <IconChevronDown class="select-arrow" />
                </div>
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="dialog-btn secondary" @click="formDialogVisible = false">取消</button>
            <button class="dialog-btn primary" @click="handleSubmit" :disabled="isSubmitting">
              {{ isSubmitting ? '处理中...' : isEditing ? '保存' : '确定' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :message="dialogMessage"
      :type="dialogType"
      :show-cancel="dialogShowCancel"
      @confirm="handleDialogConfirm"
    />

    <Transition name="modal">
      <div
        v-if="testDialogVisible"
        class="models-modal-overlay"
        @click.self="testDialogVisible = false"
      >
        <div class="test-dialog">
          <div class="dialog-header">
            <h3>测试结果</h3>
            <button class="close-btn" @click="testDialogVisible = false" aria-label="关闭">
              <IconClose />
            </button>
          </div>

          <div class="dialog-body test-dialog-body">
            <div v-if="modelsStore.testResult" class="test-result">
              <div
                class="test-status"
                :class="modelsStore.testResult.success ? 'success' : 'error'"
              >
                <IconSuccess v-if="modelsStore.testResult.success" />
                <IconError v-else />
                <span>{{ modelsStore.testResult.message }}</span>
              </div>

              <div v-if="modelsStore.testResult.response" class="test-response">
                <div class="response-label">模型响应:</div>
                <div class="response-content">
                  <MarkdownRenderer :content="formatTestResponse(modelsStore.testResult.response)" />
                </div>
              </div>

              <div v-if="modelsStore.testResult.latency" class="test-latency">
                响应时间: {{ modelsStore.testResult.latency }}秒
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="dialog-btn primary" @click="testDialogVisible = false">确定</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="toast">
      <div v-if="toastVisible" class="toast" :class="`toast-${toastType}`">
        <IconSuccess v-if="toastType === 'success'" />
        <IconWarning v-else-if="toastType === 'warning'" />
        <IconInfo v-else />
        <span>{{ toastMessage }}</span>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useModelsStore } from '@/stores'
import { API_PROVIDERS, PROVIDER_NAMES, PROVIDER_OPTIONS, getModelCapabilities } from '@/constants'
import type { ModelConfig } from '@/types'
import Dialog from '@/components/common/Dialog.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import {
  IconClose,
  IconSuccess,
  IconWarning,
  IconError,
  IconAdd,
  IconEdit,
  IconDelete,
  IconCopy,
  IconLink,
  IconChevronDown,
  IconDisable,
} from '@/components/icons'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const modelsStore = useModelsStore()

const providerConfig = API_PROVIDERS
const providerNames = PROVIDER_NAMES
const providerOptions = PROVIDER_OPTIONS

function getCapabilities(modelName: string) {
  return getModelCapabilities(modelName)
}

const formDialogVisible = ref(false)
const testDialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const isSubmitting = ref(false)
const isTestingModel = ref(false)
const testingModelName = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')
const dialogType = ref<'info' | 'success' | 'warning' | 'error'>('info')
const dialogShowCancel = ref(false)
const dialogCallback = ref<(() => void) | null>(null)

const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error' | 'warning'>('success')
let toastTimer: ReturnType<typeof setTimeout> | null = null

const formData = reactive({
  providerId: 'deepseek',
  name: '',
  baseUrl: 'https://api.deepseek.com',
  apiKey: '',
  modelName: 'deepseek-chat',
})

const originalApiKey = ref('')
const apiKeyChanged = ref(false)

const availableModels = computed(() => {
  return providerConfig[formData.providerId]?.models || []
})

watch(
  () => formData.apiKey,
  newVal => {
    if (isEditing.value && originalApiKey.value) {
      apiKeyChanged.value = newVal !== originalApiKey.value
    }
  }
)

function showToast(message: string, type: 'success' | 'error' | 'warning' = 'success') {
  if (toastTimer) {
    clearTimeout(toastTimer)
  }
  toastMessage.value = message
  toastType.value = type
  toastVisible.value = true
  toastTimer = setTimeout(() => {
    toastVisible.value = false
    toastTimer = null
  }, 2500)
}

function handleProviderChange() {
  const config = providerConfig[formData.providerId]
  if (config) {
    formData.baseUrl = config.baseUrl
    formData.modelName = config.models[0]?.value || ''
  }
}

function openApiKeyPage() {
  const url = providerConfig[formData.providerId]?.apiKeyUrl
  if (url) {
    window.open(url, '_blank')
  }
}

function handleClose() {
  emit('close')
}

function showDialog(
  title: string,
  message: string,
  type: 'info' | 'success' | 'warning' | 'error' = 'info',
  showCancel = false,
  callback?: () => void
) {
  dialogTitle.value = title
  dialogMessage.value = message
  dialogType.value = type
  dialogShowCancel.value = showCancel
  dialogCallback.value = callback || null
  dialogVisible.value = true
}

function handleDialogConfirm() {
  if (dialogCallback.value) {
    dialogCallback.value()
    dialogCallback.value = null
  }
}

function showAddDialog() {
  isEditing.value = false
  editingId.value = null
  formData.providerId = 'deepseek'
  formData.name = ''
  formData.baseUrl = 'https://api.deepseek.com'
  formData.apiKey = ''
  formData.modelName = 'deepseek-chat'
  formDialogVisible.value = true
}

function handleEdit(model: ModelConfig) {
  isEditing.value = true
  editingId.value = model.id
  formData.providerId = model.providerId || 'custom'
  formData.name = model.name
  formData.baseUrl = model.baseUrl
  formData.apiKey = model.apiKey
  originalApiKey.value = model.apiKey
  apiKeyChanged.value = false
  formDialogVisible.value = true
}

async function handleClone(model: ModelConfig) {
  isEditing.value = false
  editingId.value = null
  formData.providerId = model.providerId || 'custom'
  formData.name = `${model.name} Copy`
  formData.baseUrl = model.baseUrl
  formData.apiKey = model.apiKey
  formData.modelName = model.modelName
  formDialogVisible.value = true
}

async function handleToggle(model: ModelConfig) {
  try {
    if (model.isEnabled) {
      await modelsStore.disableModel(model.id)
      showToast('模型已禁用', 'success')
    } else {
      if (!model.apiKey) {
        showDialog('无法启用', '请先配置 API 密钥', 'warning')
        return
      }
      const result = await modelsStore.enableModel(model.id)
      if (!result.success) {
        showDialog('启用失败', result.message, 'error')
        return
      }
      showToast('模型已启用', 'success')
    }
  } catch {
    showDialog('操作失败', '请稍后重试', 'error')
  }
}

async function handleDelete(modelId: string) {
  showDialog(
    '确认删除',
    '确定要删除这个模型配置吗？此操作不可撤销。',
    'warning',
    true,
    async () => {
      try {
        await modelsStore.deleteModelSilent(modelId)
        showToast('模型已删除', 'success')
      } catch {
        showDialog('删除失败', '请稍后重试', 'error')
      }
    }
  )
}

async function handleTest(model: ModelConfig) {
  if (!model.apiKey) {
    showToast('请先配置 API 密钥', 'warning')
    return
  }

  isTestingModel.value = true
  testingModelName.value = model.name

  try {
    await modelsStore.testModelById(model.id)
    testDialogVisible.value = true
  } catch {
    showDialog('测试失败', '请检查网络连接和 API 配置', 'error')
  } finally {
    isTestingModel.value = false
    testingModelName.value = ''
  }
}

function handleTestTimeout() {
  isTestingModel.value = false
  testingModelName.value = ''
  showDialog('测试超时', '连接超时，请检查网络或稍后重试', 'warning')
}

async function handleSubmit() {
  if (!isEditing.value && !formData.apiKey.trim()) {
    showDialog('提示', '请输入 API 密钥', 'warning')
    return
  }

  const selectedModel = availableModels.value.find(m => m.value === formData.modelName)
  const modelType = selectedModel?.modelType || 'text'

  const config: Omit<ModelConfig, 'id'> & { apiKeyUnchanged?: boolean } = {
    providerId: formData.providerId,
    name: formData.name.trim() || '',
    baseUrl: formData.baseUrl,
    apiKey: formData.apiKey,
    modelName: formData.modelName,
    modelType: modelType,
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
      formDialogVisible.value = false
      showToast('模型已更新', 'success')
      await modelsStore.loadModels()
    } else {
      await modelsStore.createModelSilent(config)
      formDialogVisible.value = false
      showToast('模型已添加', 'success')
      await modelsStore.loadModels()
    }
  } catch {
    showDialog('操作失败', '请稍后重试', 'error')
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

function formatTestResponse(response: string): string {
  if (!response) return ''
  return response
    .replace(
      /\*\*推理过程:\*\*\n([\s\S]*?)(?=\n\n\*\*回答:\*\*|\n\n---|\n\n$|$)/g,
      (_, reasoning) => {
        return `<div class="reasoning-block"><div class="reasoning-label">推理过程</div><div class="reasoning-content">${reasoning.trim()}</div></div>\n\n`
      }
    )
    .replace(/\*\*回答:\*\*\n?/g, '<div class="answer-label">回答</div>\n\n')
}

onMounted(async () => {
  if (props.visible) {
    await modelsStore.loadModels()
  }
})

onUnmounted(() => {
  if (toastTimer) {
    clearTimeout(toastTimer)
    toastTimer = null
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

.model-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  min-height: 72px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s ease-out;

  &:hover {
    background: #f9fafb;
  }

  &:last-child {
    border-bottom: none;
  }
}

.card-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.model-name {
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: #333333;
  line-height: 22px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-tags {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;

  &::-webkit-scrollbar {
    display: none;
  }
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: var(--font-size-xs);
  font-weight: 400;
  line-height: 16px;
  white-space: nowrap;
  flex-shrink: 0;

  &.tag-provider {
    background: #f3e8ff;
    color: #9333ea;
  }

  &.tag-model {
    background: #dbeafe;
    color: #3b82f6;
  }

  &.tag-tool {
    background: #d1fae5;
    color: #10b981;
  }

  &.tag-reasoning {
    background: #fef3c7;
    color: #ff9500;
  }

  &.tag-websearch {
    background: #e0f2fe;
    color: #0284c7;
  }

  &.tag-multimodal {
    background: #fce7f3;
    color: #db2777;
  }

  &.tag-enabled {
    background: #d1fae5;
    color: #10b981;
  }

  &.tag-disabled {
    background: #f3f4f6;
    color: #9ca3af;
  }
}

.card-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  margin-left: 16px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: var(--font-size-xs);
  color: #666666;
  cursor: pointer;
  transition: all 0.2s;

  svg {
    width: 14px;
    height: 14px;
  }

  &:hover:not(:disabled) {
    background: #f3f4f6;
    color: #333333;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.enable-btn {
    color: #10b981;

    &:hover {
      background: #d1fae5;
    }
  }

  &.disable-btn {
    color: #ff9500;

    &:hover {
      background: #fef3c7;
    }
  }

  &.delete-btn {
    color: #ef4444;

    &:hover {
      background: #fee2e2;
    }
  }
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

.form-section {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }

  .section-title {
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: #333333;
    margin-bottom: 12px;
    line-height: 20px;
  }
}

.form-item {
  margin-bottom: 8px;

  &:last-child {
    margin-bottom: 0;
  }
}

.form-label {
  display: block;
  font-size: var(--font-size-xs);
  font-weight: 400;
  color: #666666;
  margin-bottom: 4px;
  line-height: 20px;
}

.form-control {
  position: relative;
  width: 100%;
}

.form-control-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.form-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  background: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: var(--font-size-xs);
  color: #333333;
  transition: all 0.2s ease-out;

  &::placeholder {
    color: #9ca3af;
  }

  &:hover {
    border-color: #9ca3af;
  }

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  }

  &:disabled {
    background: #e5e7eb;
    color: #9ca3af;
    cursor: not-allowed;
  }
}

.form-select {
  width: 100%;
  height: 40px;
  padding: 0 36px 0 12px;
  background: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: var(--font-size-xs);
  color: #333333;
  cursor: pointer;
  appearance: none;
  transition: all 0.2s ease-out;

  &:hover {
    border-color: #9ca3af;
  }

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  }
}

.select-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: #666666;
  pointer-events: none;
  transition: transform 0.2s ease;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  color: #666666;
  transition: all 0.2s;
  flex-shrink: 0;

  svg {
    width: 16px;
    height: 16px;
  }

  &:hover {
    background: #f3f4f6;
    color: #333333;
  }
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

.test-dialog {
  background: #ffffff;
  border-radius: 12px;
  width: 560px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.test-dialog-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 24px;
}

.test-result {
  .test-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    border-radius: 8px;
    font-size: var(--font-size-xs);

    svg {
      width: 20px;
      height: 20px;
    }

    &.success {
      background: #d1fae5;
      color: #10b981;
    }

    &.error {
      background: #fee2e2;
      color: #ef4444;
    }
  }

  .test-response {
    margin-top: 16px;

    .response-label {
      font-size: var(--font-size-xs);
      font-weight: 500;
      color: #666666;
      margin-bottom: 8px;
    }

    .response-content {
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 12px 16px;
      max-height: 400px;
      overflow-y: auto;

      .markdown-content {
        font-size: var(--font-size-sm);
        line-height: 1.6;
      }
    }
  }

  .test-latency {
    margin-top: 12px;
    font-size: 13px;
    color: #666666;
  }
}

.toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #1f2937;
  color: #ffffff;
  border-radius: 8px;
  font-size: 14px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  z-index: 4000;

  svg {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
  }

  &.toast-success {
    background: #10b981;
  }

  &.toast-error {
    background: #ef4444;
  }

  &.toast-warning {
    background: #f59e0b;
  }
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;

  .models-modal,
  .form-dialog,
  .test-dialog {
    transition:
      transform 0.25s ease,
      opacity 0.25s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .models-modal,
  .form-dialog,
  .test-dialog {
    transform: scale(0.95) translateY(-20px);
    opacity: 0;
  }
}
</style>
