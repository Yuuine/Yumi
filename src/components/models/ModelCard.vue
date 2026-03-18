<template>
  <div class="model-card">
    <div class="card-left">
      <div class="model-name">{{ model.name }}</div>
      <div class="model-tags">
        <span class="tag tag-provider">
          {{ providerNames[model.providerId] || model.providerId }}
        </span>
        <span class="tag tag-model">{{ model.modelName }}</span>
        <span v-if="capabilities.toolCall" class="tag tag-tool">工具调用</span>
        <span v-if="capabilities.reasoning" class="tag tag-reasoning">推理模式</span>
        <span v-if="capabilities.webSearch" class="tag tag-websearch">联网搜索</span>
        <span v-if="capabilities.multimodal" class="tag tag-multimodal">多模态</span>
        <span v-if="model.isEnabled" class="tag tag-enabled">已启用</span>
        <span v-else class="tag tag-disabled">已禁用</span>
      </div>
    </div>

    <div class="card-right">
      <button class="action-btn" @click="emit('test')" :disabled="isTesting" type="button">
        <IconLink :stroke-width="1.5" />
        <span>测试</span>
      </button>
      <button class="action-btn" @click="emit('edit')" :disabled="isTesting" type="button">
        <IconEdit :stroke-width="1.5" />
        <span>编辑</span>
      </button>
      <button class="action-btn" @click="emit('clone')" :disabled="isTesting" type="button">
        <IconCopy :stroke-width="1.5" />
        <span>克隆</span>
      </button>
      <button
        class="action-btn"
        :class="model.isEnabled ? 'disable-btn' : 'enable-btn'"
        @click="emit('toggle')"
        :disabled="isTesting"
        type="button"
      >
        <IconDisable v-if="model.isEnabled" :stroke-width="1.5" />
        <IconSuccess v-else :stroke-width="1.5" />
        <span>{{ model.isEnabled ? '禁用' : '启用' }}</span>
      </button>
      <button
        class="action-btn delete-btn"
        @click="emit('delete')"
        :disabled="isTesting"
        type="button"
      >
        <IconDelete :stroke-width="1.5" />
        <span>删除</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ModelConfig } from '@/types'
import { PROVIDER_NAMES, getModelCapabilities } from '@/constants'
import {
  IconLink,
  IconEdit,
  IconCopy,
  IconDelete,
  IconDisable,
  IconSuccess,
} from '@/components/icons'

interface Props {
  model: ModelConfig
  isTesting?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isTesting: false,
})

const emit = defineEmits<{
  test: []
  edit: []
  clone: []
  toggle: []
  delete: []
}>()

const providerNames = PROVIDER_NAMES

const capabilities = computed(() => getModelCapabilities(props.model.modelName))
</script>

<style lang="scss" scoped>
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
</style>
