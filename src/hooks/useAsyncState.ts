import { ref, computed, type Ref, type ComputedRef } from 'vue'

/**
 * 异步状态接口
 * @template T - 数据类型
 */
export interface AsyncState<T> {
  /** 响应式数据 */
  data: Ref<T | null>
  /** 响应式加载状态 */
  loading: Ref<boolean>
  /** 响应式错误对象 */
  error: Ref<Error | null>
  /** 是否已完成（成功或失败） */
  isReady: ComputedRef<boolean>
  /** 是否有错误 */
  hasError: ComputedRef<boolean>
  /** 执行异步操作 */
  execute: () => Promise<T | null>
  /** 重置状态 */
  reset: () => void
}

/**
 * 异步状态配置选项
 * @template T - 数据类型
 */
export interface AsyncStateOptions<T> {
  /** 初始值 */
  initialValue?: T
  /** 是否立即执行 */
  immediate?: boolean
  /** 执行前的回调，返回 false 可阻止执行 */
  onBefore?: () => boolean | void
  /** 执行成功后的回调 */
  onSuccess?: (data: T) => void
  /** 执行失败后的回调 */
  onError?: (error: Error) => void
  /** 执行完成后的回调（无论成功或失败） */
  onFinally?: () => void
}

/**
 * 异步状态管理 Hook
 *
 * 用于封装异步操作的状态管理，提供统一的 loading、error、data 状态管理。
 * 支持泛型、回调钩子和状态重置功能。
 *
 * @template T - 异步操作返回的数据类型
 * @param asyncFn - 要执行的异步函数
 * @param options - 配置选项
 * @returns 异步状态管理对象
 *
 * @example
 * ```typescript
 * // 基础用法
 * const { data, loading, error, execute } = useAsyncState(
 *   () => fetchUserInfo(userId)
 * )
 *
 * // 带初始值和回调
 * const state = useAsyncState(
 *   () => fetchUserList(),
 *   {
 *     initialValue: [],
 *     onSuccess: (data) => console.log('获取成功:', data),
 *     onError: (err) => console.error('获取失败:', err)
 *   }
 * )
 *
 * // 立即执行
 * const { data, loading } = useAsyncState(
 *   () => fetchConfig(),
 *   { immediate: true }
 * )
 * ```
 */
export function useAsyncState<T>(
  asyncFn: () => Promise<T>,
  options?: AsyncStateOptions<T>
): AsyncState<T> {
  const { initialValue, immediate = false, onBefore, onSuccess, onError, onFinally } = options || {}

  const data = ref<T | null>(initialValue ?? null) as Ref<T | null>
  const loading = ref<boolean>(false)
  const error = ref<Error | null>(null)

  const isReady = computed<boolean>(() => {
    return !loading.value && (data.value !== null || error.value !== null)
  })

  const hasError = computed<boolean>(() => {
    return error.value !== null
  })

  /**
   * 执行异步操作
   * @returns 异步操作的结果数据，失败时返回 null
   */
  async function execute(): Promise<T | null> {
    if (onBefore) {
      const shouldProceed = onBefore()
      if (shouldProceed === false) {
        return null
      }
    }

    loading.value = true
    error.value = null

    try {
      const result = await asyncFn()
      data.value = result
      onSuccess?.(result)
      return result
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error(String(err))
      error.value = errorObj
      onError?.(errorObj)
      return null
    } finally {
      loading.value = false
      onFinally?.()
    }
  }

  /**
   * 重置状态到初始值
   */
  function reset(): void {
    data.value = initialValue ?? null
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
    isReady,
    hasError,
    execute,
    reset,
  }
}
