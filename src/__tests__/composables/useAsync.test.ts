import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAsync } from '@/composables/useAsync'

describe('useAsync - 异步操作', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('基础状态', () => {
    it('初始化状态正确', () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      const { data, loading, error } = useAsync(asyncFn)

      expect(data.value).toBeNull()
      expect(loading.value).toBe(false)
      expect(error.value).toBeNull()
    })
  })

  describe('execute 方法', () => {
    it('成功执行异步函数', async () => {
      const asyncFn = vi.fn().mockResolvedValue('成功结果')
      const { data, loading, error, execute } = useAsync(asyncFn)

      const promise = execute()
      expect(loading.value).toBe(true)

      const result = await promise
      expect(loading.value).toBe(false)
      expect(error.value).toBeNull()
      expect(data.value).toBe('成功结果')
      expect(result).toBe('成功结果')
      expect(asyncFn).toHaveBeenCalledTimes(1)
    })

    it('处理异步函数失败', async () => {
      const testError = new Error('测试错误')
      const asyncFn = vi.fn().mockRejectedValue(testError)
      const { data, loading, error, execute } = useAsync(asyncFn)

      const result = await execute()
      expect(loading.value).toBe(false)
      expect(data.value).toBeNull()
      expect(error.value).toEqual(testError)
      expect(result).toBeNull()
    })

    it('处理非 Error 类型的错误', async () => {
      const asyncFn = vi.fn().mockRejectedValue('字符串错误')
      const { error, execute } = useAsync(asyncFn)

      await execute()
      expect(error.value).toBeInstanceOf(Error)
      expect(error.value?.message).toBe('字符串错误')
    })

    it('传递参数给异步函数', async () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      const { execute } = useAsync(asyncFn)

      await execute('arg1', 'arg2', 123)
      expect(asyncFn).toHaveBeenCalledWith('arg1', 'arg2', 123)
    })
  })

  describe('回调函数', () => {
    it('成功时调用 onSuccess', async () => {
      const onSuccess = vi.fn()
      const asyncFn = vi.fn().mockResolvedValue('成功结果')
      const { execute } = useAsync(asyncFn, { onSuccess })

      await execute()
      expect(onSuccess).toHaveBeenCalledWith('成功结果')
    })

    it('失败时调用 onError', async () => {
      const onError = vi.fn()
      const testError = new Error('测试错误')
      const asyncFn = vi.fn().mockRejectedValue(testError)
      const { execute } = useAsync(asyncFn, { onError })

      await execute()
      expect(onError).toHaveBeenCalledWith(testError)
    })
  })

  describe('reset 方法', () => {
    it('重置所有状态', async () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      const { data, loading, error, execute, reset } = useAsync(asyncFn)

      await execute()
      expect(data.value).not.toBeNull()

      reset()
      expect(data.value).toBeNull()
      expect(loading.value).toBe(false)
      expect(error.value).toBeNull()
    })
  })

  describe('immediate 选项', () => {
    it('immediate 为 true 时自动执行', async () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      useAsync(asyncFn, { immediate: true })

      expect(asyncFn).toHaveBeenCalledTimes(1)
    })

    it('immediate 默认为 false', () => {
      const asyncFn = vi.fn().mockResolvedValue('test')
      useAsync(asyncFn)

      expect(asyncFn).not.toHaveBeenCalled()
    })
  })
})
