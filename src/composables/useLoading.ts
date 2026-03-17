/**
 * 加载状态管理 Hook
 */
import { ref, type Ref } from 'vue'

interface UseLoadingReturn {
  loading: Ref<boolean>
  startLoading: () => void
  stopLoading: () => void
  withLoading: <T>(fn: () => Promise<T>) => Promise<T>
}

export function useLoading(initialState = false): UseLoadingReturn {
  const loading = ref(initialState)

  function startLoading(): void {
    loading.value = true
  }

  function stopLoading(): void {
    loading.value = false
  }

  async function withLoading<T>(fn: () => Promise<T>): Promise<T> {
    try {
      startLoading()
      return await fn()
    } finally {
      stopLoading()
    }
  }

  return { loading, startLoading, stopLoading, withLoading }
}
