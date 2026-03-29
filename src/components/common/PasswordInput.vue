<template>
  <div class="password-input-wrap">
    <input
      v-model="inputValue"
      :type="showPassword ? 'text' : 'password'"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      @input="handleInput"
    />
    <button type="button" class="eye-btn" @click="togglePassword">
      <svg
        v-if="!showPassword"
        viewBox="0 0 20 20"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z" />
        <circle cx="10" cy="10" r="2.5" />
      </svg>
      <svg v-else viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M15 15a6 6 0 01-10 0M5 5a6 6 0 0110 0" />
        <line x1="1" y1="1" x2="19" y2="19" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  modelValue: string
  placeholder?: string
  autocomplete?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
  autocomplete: 'current-password',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const showPassword = ref(false)
const inputValue = ref(props.modelValue)

watch(
  () => props.modelValue,
  newValue => {
    inputValue.value = newValue
  }
)

function togglePassword(): void {
  showPassword.value = !showPassword.value
}

function handleInput(event: Event): void {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<style lang="scss" scoped>
.password-input-wrap {
  position: relative;

  input {
    width: 100%;
    padding: 14px 16px;
    padding-right: 44px;
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    font-size: 15px;
    color: white;
    outline: none;
    transition: all 0.2s ease;
    box-sizing: border-box;

    &::placeholder {
      color: rgba(255, 255, 255, 0.6);
    }

    &:focus {
      background: rgba(255, 255, 255, 0.25);
      border-color: rgba(255, 255, 255, 0.5);
    }
  }
}

.eye-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  padding: 4px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: color 0.2s;

  &:hover {
    color: white;
  }

  svg {
    width: 18px;
    height: 18px;
  }
}
</style>
