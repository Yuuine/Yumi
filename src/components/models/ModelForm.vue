<template>
  <div class="form-section">
    <div class="section-title">提供商配置</div>

    <div class="form-item">
      <label class="form-label">提供商</label>
      <div class="form-control">
        <select v-model="formData.providerId" class="form-select" @change="handleProviderChange">
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
          :type="showApiKey ? 'text' : 'password'"
          class="form-input"
          placeholder="输入 API 密钥"
        />
        <button class="icon-btn" title="切换显示" @click="showApiKey = !showApiKey" type="button">
          <IconLink v-if="showApiKey" :stroke-width="1.5" />
          <IconCopy v-else :stroke-width="1.5" />
        </button>
        <button
          class="icon-btn"
          title="前往获取 API 密钥"
          @click="openApiKeyPage"
          type="button"
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
          <option v-for="model in availableModels" :key="model.value" :value="model.value">
            {{ model.label }}
          </option>
        </select>
        <IconChevronDown class="select-arrow" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { API_PROVIDERS, PROVIDER_OPTIONS } from '@/constants'
import type { ModelConfig } from '@/types'
import { IconChevronDown, IconLink, IconCopy } from '@/components/icons'

interface ModelFormData {
  providerId: string
  name: string
  baseUrl: string
  apiKey: string
  modelName: string
}

const props = withDefaults(
  defineProps<{
    modelValue?: Partial<ModelFormData>
    isEditing?: boolean
    originalApiKey?: string
  }>(),
  {
    modelValue: () => ({}),
    isEditing: false,
    originalApiKey: '',
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: ModelFormData]
  'apiKeyChanged': [changed: boolean]
}>()

const providerConfig = API_PROVIDERS
const providerOptions = PROVIDER_OPTIONS

const showApiKey = ref(false)

const formData = ref<ModelFormData>({
  providerId: 'deepseek',
  name: '',
  baseUrl: 'https://api.deepseek.com',
  apiKey: '',
  modelName: 'deepseek-chat',
  ...props.modelValue,
})

const availableModels = computed(() => {
  return providerConfig[formData.value.providerId]?.models || []
})

const apiKeyChanged = computed(() => {
  if (props.isEditing && props.originalApiKey) {
    return formData.value.apiKey !== props.originalApiKey
  }
  return true
})

watch(
  formData,
  (newVal) => {
    emit('update:modelValue', newVal)
  },
  { deep: true }
)

watch(apiKeyChanged, (changed) => {
  emit('apiKeyChanged', changed)
})

function handleProviderChange(): void {
  const config = providerConfig[formData.value.providerId]
  if (config) {
    formData.value.baseUrl = config.baseUrl
    formData.value.modelName = config.models[0]?.value || ''
  }
}

function openApiKeyPage(): void {
  const url = providerConfig[formData.value.providerId]?.apiKeyUrl
  if (url) {
    window.open(url, '_blank')
  }
}

function reset(): void {
  formData.value = {
    providerId: 'deepseek',
    name: '',
    baseUrl: 'https://api.deepseek.com',
    apiKey: '',
    modelName: 'deepseek-chat',
  }
  showApiKey.value = false
}

function setFormData(data: Partial<ModelConfig>): void {
  formData.value = {
    providerId: data.providerId || 'custom',
    name: data.name || '',
    baseUrl: data.baseUrl || '',
    apiKey: data.apiKey || '',
    modelName: data.modelName || '',
  }
}

defineExpose({
  reset,
  setFormData,
  formData,
  apiKeyChanged,
})
</script>

<style lang="scss" scoped>
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
</style>
