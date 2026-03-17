/**
 * 剪贴板操作 Hook
 */
import { ref, type Ref } from 'vue'
import { copyToClipboard } from '@/utils'

interface UseClipboardReturn {
  copied: Ref<boolean>
  copy: (text: string) => Promise<boolean>
}

export function useClipboard(): UseClipboardReturn {
  const copied = ref(false)

  async function copy(text: string): Promise<boolean> {
    const success = await copyToClipboard(text)
    if (success) {
      copied.value = true
      setTimeout(() => {
        copied.value = false
      }, 2000)
    }
    return success
  }

  return { copied, copy }
}
