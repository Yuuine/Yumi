import { ref, type Ref } from 'vue'

interface UseAsyncReturn<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<Error | null>
  execute: (...args: unknown[]) => Promise<T | null>
  reset: () => void
}

export function useAsync<T>(
  asyncFn: (...args: unknown[]) => Promise<T>,
  options?: {
    immediate?: boolean
    onSuccess?: (data: T) => void
    onError?: (error: Error) => void
  }
): UseAsyncReturn<T> {
  const { immediate = false, onSuccess, onError } = options || {}

  const data = ref<T | null>(null) as Ref<T | null>
  const loading = ref(false)
  const error = ref<Error | null>(null)

  async function execute(...args: unknown[]): Promise<T | null> {
    loading.value = true
    error.value = null

    try {
      const result = await asyncFn(...args)
      data.value = result
      onSuccess?.(result)
      return result
    } catch (err) {
      const asyncError = err instanceof Error ? err : new Error(String(err))
      error.value = asyncError
      onError?.(asyncError)
      return null
    } finally {
      loading.value = false
    }
  }

  function reset(): void {
    data.value = null
    loading.value = false
    error.value = null
  }

  if (immediate) {
    execute()
  }

  return {
    data,
    loading,
    error,
    execute,
    reset,
  }
}
