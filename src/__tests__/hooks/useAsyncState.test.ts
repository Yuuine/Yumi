import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAsyncState } from '@/hooks/useAsyncState'

describe('useAsyncState - 异步状态 Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('基础状态', () => {
    it('初始化状态正确', () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      const state = useAsyncState(asyncFn)

      expect(state.data.value).toBeNull()
      expect(state.loading.value).toBe(false)
      expect(state.error.value).toBeNull()
      expect(state.isReady.value).toBe(false)
      expect(state.hasError.value).toBe(false)
    })

    it('使用初始值初始化', () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      const state = useAsyncState(asyncFn, { initialValue: 'initial' })

      expect(state.data.value).toBe('initial')
    })
  })

  describe('execute 方法', () => {
    it('成功执行异步操作', async () => {
      const asyncFn = vi.fn().mockResolvedValue('成功结果')
      const state = useAsyncState(asyncFn)

      const promise = state.execute()
      expect(state.loading.value).toBe(true)

      const result = await promise
      expect(state.loading.value).toBe(false)
      expect(state.error.value).toBeNull()
      expect(state.data.value).toBe('成功结果')
      expect(state.isReady.value).toBe(true)
      expect(state.hasError.value).toBe(false)
      expect(result).toBe('成功结果')
      expect(asyncFn).toHaveBeenCalledTimes(1)
    })

    it('处理异步操作失败', async () => {
      const testError = new Error('测试错误')
      const asyncFn = vi.fn().mockRejectedValue(testError)
      const state = useAsyncState(asyncFn)

      const result = await state.execute()
      expect(state.loading.value).toBe(false)
      expect(state.data.value).toBeNull()
      expect(state.error.value).toEqual(testError)
      expect(state.isReady.value).toBe(true)
      expect(state.hasError.value).toBe(true)
      expect(result).toBeNull()
    })

    it('处理非 Error 类型的错误', async () => {
      const asyncFn = vi.fn().mockRejectedValue('字符串错误')
      const state = useAsyncState(asyncFn)

      await state.execute()
      expect(state.error.value).toBeInstanceOf(Error)
      expect(state.error.value?.message).toBe('字符串错误')
    })
  })

  describe('回调函数', () => {
    it('成功时调用 onSuccess', async () => {
      const onSuccess = vi.fn()
      const asyncFn = vi.fn().mockResolvedValue('成功结果')
      const state = useAsyncState(asyncFn, { onSuccess })

      await state.execute()
      expect(onSuccess).toHaveBeenCalledWith('成功结果')
    })

    it('失败时调用 onError', async () => {
      const onError = vi.fn()
      const testError = new Error('测试错误')
      const asyncFn = vi.fn().mockRejectedValue(testError)
      const state = useAsyncState(asyncFn, { onError })

      await state.execute()
      expect(onError).toHaveBeenCalledWith(testError)
    })

    it('无论成功或失败都调用 onFinally', async () => {
      const onFinally = vi.fn()
      const asyncFn1 = vi.fn().mockResolvedValue('成功')
      const asyncFn2 = vi.fn().mockRejectedValue(new Error('失败'))

      const state1 = useAsyncState(asyncFn1, { onFinally })
      await state1.execute()
      expect(onFinally).toHaveBeenCalledTimes(1)

      onFinally.mockClear()

      const state2 = useAsyncState(asyncFn2, { onFinally })
      await state2.execute()
      expect(onFinally).toHaveBeenCalledTimes(1)
    })

    it('onBefore 返回 false 时阻止执行', async () => {
      const onBefore = vi.fn().mockReturnValue(false)
      const asyncFn = vi.fn().mockResolvedValue('test')
      const state = useAsyncState(asyncFn, { onBefore })

      const result = await state.execute()
      expect(onBefore).toHaveBeenCalled()
      expect(asyncFn).not.toHaveBeenCalled()
      expect(result).toBeNull()
    })

    it('onBefore 返回 true 或 undefined 时正常执行', async () => {
      const onBefore1 = vi.fn().mockReturnValue(true)
      const onBefore2 = vi.fn().mockReturnValue(undefined)
      const asyncFn = vi.fn().mockResolvedValue('test')

      const state1 = useAsyncState(asyncFn, { onBefore: onBefore1 })
      await state1.execute()
      expect(asyncFn).toHaveBeenCalledTimes(1)

      asyncFn.mockClear()

      const state2 = useAsyncState(asyncFn, { onBefore: onBefore2 })
      await state2.execute()
      expect(asyncFn).toHaveBeenCalledTimes(1)
    })
  })

  describe('reset 方法', () => {
    it('重置所有状态', async () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      const state = useAsyncState(asyncFn)

      await state.execute()
      expect(state.data.value).not.toBeNull()

      state.reset()
      expect(state.data.value).toBeNull()
      expect(state.loading.value).toBe(false)
      expect(state.error.value).toBeNull()
      expect(state.isReady.value).toBe(false)
      expect(state.hasError.value).toBe(false)
    })

    it('重置时使用初始值', async () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      const state = useAsyncState(asyncFn, { initialValue: 'initial' })

      await state.execute()
      expect(state.data.value).toBe('test')

      state.reset()
      expect(state.data.value).toBe('initial')
    })
  })

  describe('immediate 选项', () => {
    it('immediate 为 true 时自动执行', async () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      useAsyncState(asyncFn, { immediate: true })

      expect(asyncFn).toHaveBeenCalledTimes(1)
    })

    it('immediate 默认为 false', () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      useAsyncState(asyncFn)

      expect(asyncFn).not.toHaveBeenCalled()
    })
  })
})
