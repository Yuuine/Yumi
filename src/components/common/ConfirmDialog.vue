<template>
  <ModalWrapper :visible="confirmDialog.visible.value" @close="confirmDialog.cancel">
    <div class="confirm-dialog">
      <div class="dialog-icon" :class="confirmDialog.type.value">
        <IconInfo v-if="confirmDialog.type.value === 'info'" />
        <IconSuccess v-else-if="confirmDialog.type.value === 'success'" />
        <IconWarning v-else-if="confirmDialog.type.value === 'warning'" />
        <IconError v-else />
      </div>
      <h3 class="dialog-title">{{ confirmDialog.title.value }}</h3>
      <p class="dialog-message">{{ confirmDialog.message.value }}</p>
      <div class="dialog-actions">
        <button
          v-if="confirmDialog.showCancel.value"
          class="btn btn-secondary"
          @click="confirmDialog.cancel"
        >
          取消
        </button>
        <button class="btn btn-primary" @click="confirmDialog.confirm">确定</button>
      </div>
    </div>
  </ModalWrapper>
</template>

<script setup lang="ts">
import { useConfirmDialog } from '@/composables/useModal'
import ModalWrapper from './ModalWrapper.vue'
import { IconInfo, IconSuccess, IconWarning, IconError } from '@/components/icons'

const confirmDialog = useConfirmDialog()
</script>

<style lang="scss" scoped>
.confirm-dialog {
  padding: 24px;
  text-align: center;
}

.dialog-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;

  &.info {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }

  &.success {
    background: rgba(34, 197, 94, 0.1);
    color: #22c55e;
  }

  &.warning {
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
  }

  &.error {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  svg {
    width: 32px;
    height: 32px;
  }
}

.dialog-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.dialog-message {
  margin: 0 0 24px;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;

  &:hover {
    background: #e5e7eb;
  }
}

.btn-primary {
  background: #7c3aed;
  color: #ffffff;

  &:hover {
    background: #6d28d9;
  }
}
</style>
