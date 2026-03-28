import { ref } from 'vue'

export function useModalState(initialVisible = false) {
  const visible = ref(initialVisible)

  function open(): void {
    visible.value = true
  }

  function close(): void {
    visible.value = false
  }

  function toggle(): void {
    visible.value = !visible.value
  }

  return {
    visible,
    open,
    close,
    toggle,
  }
}
