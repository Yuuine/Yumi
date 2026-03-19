<template>
  <Transition name="fade">
    <button
      v-if="visible"
      class="scroll-to-bottom"
      @click="handleClick"
      type="button"
      title="滚动到底部"
    >
      <IconChevronDown class="icon" />
    </button>
  </Transition>
</template>

<script setup lang="ts">
import { IconChevronDown } from '@/components/icons'

interface Props {
  visible?: boolean
}

withDefaults(defineProps<Props>(), {
  visible: false,
})

const emit = defineEmits<{
  click: []
}>()

function handleClick() {
  emit('click')
}
</script>

<style lang="scss" scoped>
.scroll-to-bottom {
  position: absolute;
  bottom: 20px;
  right: 24px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12), 0 1px 3px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;

  &:hover {
    background: #ffffff;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.16), 0 2px 6px rgba(0, 0, 0, 0.1);
    transform: scale(1.05);
  }

  &:active {
    transform: scale(0.95);
  }

  .icon {
    width: 22px;
    height: 22px;
    color: #333333;
    filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.1));
  }
}

[data-theme='dark'] .scroll-to-bottom {
  background: rgba(31, 31, 31, 0.95);
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3), 0 1px 3px rgba(0, 0, 0, 0.2);

  &:hover {
    background: rgba(42, 42, 42, 0.98);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4), 0 2px 6px rgba(0, 0, 0, 0.25);
  }

  .icon {
    color: #e5eaf3;
    filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.2));
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scale(0.8);
}
</style>
