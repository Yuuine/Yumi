<template>
  <button
    class="toggle-switch"
    :class="{ active: modelValue, disabled }"
    :disabled="disabled"
    type="button"
    @click="handleToggle"
  >
    <span class="toggle-knob"></span>
  </button>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean
    disabled?: boolean
  }>(),
  {
    disabled: false,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  change: [value: boolean]
}>()

function handleToggle(): void {
  if (props.disabled) {
    return
  }

  const nextValue = !props.modelValue
  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}
</script>

<style scoped lang="scss">
.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  background: var(--border-color, #d1d5db);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;

  &.active {
    background: var(--color-success, #10b981);
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: var(--bg-primary, #ffffff);
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: var(--shadow-sm, 0 2px 4px rgba(0, 0, 0, 0.1));
}

.toggle-switch.active .toggle-knob {
  transform: translateX(20px);
}
</style>
