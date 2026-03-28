<template>
  <div class="starry-bg">
    <div class="stars">
      <div v-for="star in starStyles" :key="star.key" class="star" :style="star.style"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  starCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  starCount: 200,
})

const starStyles = computed(() => {
  return Array.from({ length: props.starCount }, (_, index) => {
    const size = Math.random() * 2 + 1
    const left = Math.random() * 100
    const top = Math.random() * 100
    const delay = Math.random() * 5
    const duration = Math.random() * 3 + 2
    return {
      key: index,
      style: {
        width: `${size}px`,
        height: `${size}px`,
        left: `${left}%`,
        top: `${top}%`,
        animationDelay: `${delay}s`,
        animationDuration: `${duration}s`,
      },
    }
  })
})
</script>

<style lang="scss" scoped>
.starry-bg {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
  overflow: hidden;
}

.stars {
  position: absolute;
  inset: 0;
}

.star {
  position: absolute;
  background: white;
  border-radius: 50%;
  animation: twinkle ease-in-out infinite;
}

@keyframes twinkle {
  0%,
  100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}
</style>
