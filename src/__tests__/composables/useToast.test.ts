import { describe, it, expect, beforeEach } from 'vitest'
import { useToast } from '@/composables/useToast'

describe('useToast - Toast 通知', () => {
  let toast: ReturnType<typeof useToast>

  beforeEach(() => {
    toast = useToast()
    toast.hide()
  })

  describe('基础状态', () => {
    it('初始化时 visible 为 false', () => {
      expect(toast.visible.value).toBe(false)
    })

    it('初始化时 message 为空', () => {
      expect(toast.message.value).toBe('')
    })

    it('初始化时 type 为 success', () => {
      expect(toast.type.value).toBe('success')
    })
  })

  describe('show 方法', () => {
    it('显示 toast 并设置正确的属性', () => {
      toast.show('测试消息', 'info')

      expect(toast.visible.value).toBe(true)
      expect(toast.message.value).toBe('测试消息')
      expect(toast.type.value).toBe('info')
    })

    it('默认类型为 success', () => {
      toast.show('默认成功消息')
      expect(toast.type.value).toBe('success')
    })
  })

  describe('快捷方法', () => {
    it('success 方法显示成功消息', () => {
      toast.success('成功！')
      expect(toast.type.value).toBe('success')
      expect(toast.message.value).toBe('成功！')
      expect(toast.visible.value).toBe(true)
    })

    it('error 方法显示错误消息', () => {
      toast.error('错误！')
      expect(toast.type.value).toBe('error')
    })

    it('warning 方法显示警告消息', () => {
      toast.warning('警告！')
      expect(toast.type.value).toBe('warning')
    })

    it('info 方法显示信息消息', () => {
      toast.info('信息！')
      expect(toast.type.value).toBe('info')
    })
  })

  describe('hide 方法', () => {
    it('立即隐藏 toast', () => {
      toast.show('测试消息')
      expect(toast.visible.value).toBe(true)

      toast.hide()
      expect(toast.visible.value).toBe(false)
    })
  })
})
