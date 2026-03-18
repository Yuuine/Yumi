import { ref, type Ref } from 'vue'

interface UseModalReturn {
  visible: Ref<boolean>
  open: () => void
  close: () => void
  toggle: () => void
}

export function useModal(initialState = false): UseModalReturn {
  const visible = ref(initialState)

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

interface UseConfirmDialogReturn {
  visible: Ref<boolean>
  title: Ref<string>
  message: Ref<string>
  type: Ref<'info' | 'success' | 'warning' | 'error'>
  showCancel: Ref<boolean>
  callback: Ref<(() => void) | null>
  confirm: () => void
  cancel: () => void
  showDialog: (
    title: string,
    message: string,
    type?: 'info' | 'success' | 'warning' | 'error',
    showCancel?: boolean,
    callback?: () => void
  ) => void
}

export function useConfirmDialog(): UseConfirmDialogReturn {
  const visible = ref(false)
  const title = ref('')
  const message = ref('')
  const type = ref<'info' | 'success' | 'warning' | 'error'>('info')
  const showCancel = ref(false)
  const callback = ref<(() => void) | null>(null)

  function showDialog(
    dialogTitle: string,
    dialogMessage: string,
    dialogType: 'info' | 'success' | 'warning' | 'error' = 'info',
    dialogShowCancel = false,
    dialogCallback?: () => void
  ): void {
    title.value = dialogTitle
    message.value = dialogMessage
    type.value = dialogType
    showCancel.value = dialogShowCancel
    callback.value = dialogCallback || null
    visible.value = true
  }

  function confirm(): void {
    if (callback.value) {
      callback.value()
      callback.value = null
    }
    visible.value = false
  }

  function cancel(): void {
    callback.value = null
    visible.value = false
  }

  return {
    visible,
    title,
    message,
    type,
    showCancel,
    callback,
    confirm,
    cancel,
    showDialog,
  }
}
