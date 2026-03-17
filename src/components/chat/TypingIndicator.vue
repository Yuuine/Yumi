<template>
  <div class="typing-indicator">
    <div class="typing-dots">
      <span></span>
      <span></span>
      <span></span>
    </div>
    <span class="typing-text">{{ roleName }} 正在思考...</span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  roleName: string
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 12px;
  width: fit-content;

  .typing-dots {
    display: flex;
    gap: 4px;

    span {
      width: 8px;
      height: 8px;
      background: var(--el-color-primary);
      border-radius: 50%;
      animation: typing 1.4s infinite ease-in-out both;

      &:nth-child(1) {
        animation-delay: -0.32s;
      }
      &:nth-child(2) {
        animation-delay: -0.16s;
      }
    }
  }

  .typing-text {
    font-size: var(--font-size-xs);
    color: var(--text-secondary);
  }
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
