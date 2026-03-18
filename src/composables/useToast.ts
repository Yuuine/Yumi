import { ref, type Ref } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastOptions {
  duration?: number
}

interface ToastState {
  visible: Ref<boolean>
  message: Ref<string>
  type: Ref<ToastType>
}

const globalState: ToastState = {
  visible: ref(false),
  message: ref(''),
  type: ref<ToastType>('success'),
}

let toastTimer: ReturnType<typeof setTimeout> | null = null

export function useToast() {
  function show(msg: string, toastType: ToastType = 'success', options: ToastOptions = {}): void {
    const { duration = 2500 } = options

    if (toastTimer) {
      clearTimeout(toastTimer)
    }

    globalState.message.value = msg
    globalState.type.value = toastType
    globalState.visible.value = true

    toastTimer = setTimeout(() => {
      globalState.visible.value = false
      toastTimer = null
    }, duration)
  }

  function success(msg: string, options?: ToastOptions): void {
    show(msg, 'success', options)
  }

  function error(msg: string, options?: ToastOptions): void {
    show(msg, 'error', options)
  }

  function warning(msg: string, options?: ToastOptions): void {
    show(msg, 'warning', options)
  }

  function info(msg: string, options?: ToastOptions): void {
    show(msg, 'info', options)
  }

  function hide(): void {
    if (toastTimer) {
      clearTimeout(toastTimer)
      toastTimer = null
    }
    globalState.visible.value = false
  }

  return {
    visible: globalState.visible,
    message: globalState.message,
    type: globalState.type,
    show,
    success,
    error,
    warning,
    info,
    hide,
  }
}
