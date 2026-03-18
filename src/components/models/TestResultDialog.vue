<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="test-dialog-overlay" @click.self="emit('close')">
        <div class="test-dialog">
          <div class="dialog-header">
            <h3>测试结果</h3>
            <button class="close-btn" @click="emit('close')" aria-label="关闭" type="button">
              <IconClose />
            </button>
          </div>

          <div class="dialog-body">
            <div v-if="result" class="test-result">
              <div class="test-status" :class="result.success ? 'success' : 'error'">
                <IconSuccess v-if="result.success" />
                <IconError v-else />
                <span>{{ result.message }}</span>
              </div>

              <div v-if="result.reasoning" class="test-reasoning">
                <div class="reasoning-label">思考过程:</div>
                <div class="reasoning-content">
                  {{ result.reasoning }}
                </div>
              </div>

              <div v-if="result.response" class="test-response">
                <div class="response-label">模型响应:</div>
                <div class="response-content">
                  <MarkdownRenderer :content="formatTestResponse(result.response)" />
                </div>
              </div>

              <div v-if="result.latency" class="test-latency">
                响应时间: {{ result.latency.toFixed(3) }}秒
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="dialog-btn primary" @click="emit('close')" type="button">确定</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import type { ModelTestResponse } from '@/types'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import { IconClose, IconSuccess, IconError } from '@/components/icons'

interface Props {
  visible: boolean
  result: ModelTestResponse | null
}

defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

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
</script>

<style lang="scss" scoped>
.test-dialog-overlay {
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

.dialog-body {
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

  .test-reasoning {
    margin-top: 16px;

    .reasoning-label {
      font-size: var(--font-size-xs);
      font-weight: 500;
      color: #999999;
      margin-bottom: 8px;
    }

    .reasoning-content {
      background: #fafafa;
      border: 1px solid #e8e8e8;
      border-radius: 8px;
      padding: 12px 16px;
      font-size: 12px;
      color: #333333;
      line-height: 1.6;
      max-height: 300px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-word;
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

  &.primary {
    background: #3b82f6;
    color: #ffffff;

    &:hover {
      background: #2563eb;
    }
  }
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;

  .test-dialog {
    transition:
      transform 0.25s ease,
      opacity 0.25s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .test-dialog {
    transform: scale(0.95) translateY(-20px);
    opacity: 0;
  }
}
</style>
