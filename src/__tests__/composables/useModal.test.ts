import { describe, it, expect, beforeEach } from 'vitest'
import { useModal, useConfirmDialog } from '@/composables/useModal'

describe('useModal - 模态框', () => {
  describe('useModal', () => {
    it('初始化时使用传入的初始状态', () => {
      const modal1 = useModal(true)
      const modal2 = useModal(false)

      expect(modal1.visible.value).toBe(true)
      expect(modal2.visible.value).toBe(false)
    })

    it('默认初始状态为 false', () => {
      const modal = useModal()
      expect(modal.visible.value).toBe(false)
    })

    it('open 方法设置 visible 为 true', () => {
      const modal = useModal(false)
      modal.open()
      expect(modal.visible.value).toBe(true)
    })

    it('close 方法设置 visible 为 false', () => {
      const modal = useModal(true)
      modal.close()
      expect(modal.visible.value).toBe(false)
    })

    it('toggle 方法切换 visible 状态', () => {
      const modal = useModal(false)

      modal.toggle()
      expect(modal.visible.value).toBe(true)

      modal.toggle()
      expect(modal.visible.value).toBe(false)
    })
  })

  describe('useConfirmDialog', () => {
    let confirmDialog: ReturnType<typeof useConfirmDialog>

    beforeEach(() => {
      confirmDialog = useConfirmDialog()
      confirmDialog.visible.value = false
    })

    it('初始化状态正确', () => {
      expect(confirmDialog.visible.value).toBe(false)
      expect(confirmDialog.title.value).toBe('')
      expect(confirmDialog.message.value).toBe('')
      expect(confirmDialog.type.value).toBe('info')
      expect(confirmDialog.showCancel.value).toBe(false)
      expect(confirmDialog.callback.value).toBeNull()
    })

    it('showDialog 方法显示对话框', () => {
      confirmDialog.showDialog('标题', '消息', 'warning', true)

      expect(confirmDialog.visible.value).toBe(true)
      expect(confirmDialog.title.value).toBe('标题')
      expect(confirmDialog.message.value).toBe('消息')
      expect(confirmDialog.type.value).toBe('warning')
      expect(confirmDialog.showCancel.value).toBe(true)
    })

    it('showDialog 方法使用默认参数', () => {
      confirmDialog.showDialog('标题', '消息')

      expect(confirmDialog.type.value).toBe('info')
      expect(confirmDialog.showCancel.value).toBe(false)
      expect(confirmDialog.callback.value).toBeNull()
    })

    it('showDialog 方法设置回调函数', () => {
      const callback = vi.fn()
      confirmDialog.showDialog('标题', '消息', 'info', true, callback)

      expect(confirmDialog.callback.value).toBe(callback)
    })

    it('confirm 方法执行回调并隐藏对话框', () => {
      const callback = vi.fn()
      confirmDialog.showDialog('标题', '消息', 'info', true, callback)
      confirmDialog.visible.value = true

      confirmDialog.confirm()

      expect(callback).toHaveBeenCalledTimes(1)
      expect(confirmDialog.callback.value).toBeNull()
      expect(confirmDialog.visible.value).toBe(false)
    })

    it('confirm 方法在没有回调时只隐藏对话框', () => {
      confirmDialog.showDialog('标题', '消息')
      confirmDialog.visible.value = true

      confirmDialog.confirm()

      expect(confirmDialog.visible.value).toBe(false)
    })

    it('cancel 方法不执行回调并隐藏对话框', () => {
      const callback = vi.fn()
      confirmDialog.showDialog('标题', '消息', 'info', true, callback)
      confirmDialog.visible.value = true

      confirmDialog.cancel()

      expect(callback).not.toHaveBeenCalled()
      expect(confirmDialog.callback.value).toBeNull()
      expect(confirmDialog.visible.value).toBe(false)
    })
  })
})
