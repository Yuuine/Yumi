<template>
  <div class="empty-state">
    <component :is="icon" v-if="icon" class="empty-icon" />
    <IconError v-else class="empty-icon" />
    <p class="empty-message">{{ message }}</p>
    <slot v-if="$slots.default" name="default"></slot>
  </div>
</template>

<script setup lang="ts">
import { type Component } from 'vue'
import { IconError } from '@/components/icons'

interface Props {
  message?: string
  icon?: Component
}

withDefaults(defineProps<Props>(), {
  message: '暂无数据',
})
</script>

<style lang="scss" scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: #9ca3af;
  margin-bottom: 16px;
}

.empty-message {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
}
</style>
