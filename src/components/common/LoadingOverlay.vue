<template>
  <Transition name="loading-overlay">
    <div
      v-if="visible"
      class="loading-overlay"
      :class="{ 'full-screen': fullScreen }"
      @click.prevent
      @mousedown.prevent
      @mouseup.prevent
    >
      <div class="loading-content">
        <div class="loading-spinner">
          <svg class="spinner-svg" viewBox="0 0 50 50">
            <circle class="spinner-path" cx="25" cy="25" r="20" fill="none" stroke-width="4" />
          </svg>
        </div>
        <div class="loading-text">{{ text }}</div>
        <div v-if="showTimeout" class="loading-timeout">已等待 {{ elapsedSeconds }}秒</div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'

interface Props {
  visible: boolean
  text?: string
  fullScreen?: boolean
  showTimeout?: boolean
  timeout?: number
}

const props = withDefaults(defineProps<Props>(), {
  text: '正在处理，请稍候...',
  fullScreen: false,
  showTimeout: false,
  timeout: 60000,
})

const emit = defineEmits<{
  timeout: []
}>()

const elapsedSeconds = ref(0)
let timer: ReturnType<typeof setInterval> | null = null
let timeoutTimer: ReturnType<typeof setTimeout> | null = null

function startTimer() {
  elapsedSeconds.value = 0
  timer = setInterval(() => {
    elapsedSeconds.value++
  }, 1000)

  if (props.timeout > 0) {
    timeoutTimer = setTimeout(() => {
      emit('timeout')
    }, props.timeout)
  }
}

function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  if (timeoutTimer) {
    clearTimeout(timeoutTimer)
    timeoutTimer = null
  }
}

watch(
  () => props.visible,
  newVal => {
    if (newVal) {
      startTimer()
    } else {
      stopTimer()
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  stopTimer()
})
</script>

<style lang="scss" scoped>
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
  cursor: wait;
  user-select: none;

  &.full-screen {
    position: fixed;
    z-index: 9999;
  }
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px 48px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.loading-spinner {
  width: 48px;
  height: 48px;
}

.spinner-svg {
  width: 100%;
  height: 100%;
  animation: spinner-rotate 2s linear infinite;
}

.spinner-path {
  stroke: #3b82f6;
  stroke-linecap: round;
  animation: spinner-dash 1.5s ease-in-out infinite;
}

@keyframes spinner-rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes spinner-dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

.loading-text {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: #333333;
  text-align: center;
}

.loading-timeout {
  font-size: var(--font-size-xs);
  color: #9ca3af;
}

.loading-overlay-enter-active,
.loading-overlay-leave-active {
  transition: opacity 0.2s ease;

  .loading-content {
    transition:
      transform 0.2s ease,
      opacity 0.2s ease;
  }
}

.loading-overlay-enter-from,
.loading-overlay-leave-to {
  opacity: 0;

  .loading-content {
    transform: scale(0.95);
    opacity: 0;
  }
}
</style>
