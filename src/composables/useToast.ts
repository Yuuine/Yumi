import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'warning'

const visible = ref(false)
const message = ref('')
const type = ref<ToastType>('success')
let timer: ReturnType<typeof setTimeout> | null = null

export function useToast() {
  function show(msg: string, t: ToastType = 'success', duration = 2500) {
    if (timer) {
      clearTimeout(timer)
    }
    message.value = msg
    type.value = t
    visible.value = true
    timer = setTimeout(() => {
      visible.value = false
      timer = null
    }, duration)
  }

  function success(msg: string) {
    show(msg, 'success')
  }

  function error(msg: string) {
    show(msg, 'error')
  }

  function warning(msg: string) {
    show(msg, 'warning')
  }

  function hide() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    visible.value = false
  }

  return {
    visible,
    message,
    type,
    show,
    success,
    error,
    warning,
    hide,
  }
}
