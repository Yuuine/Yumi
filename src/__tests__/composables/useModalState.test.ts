import { describe, it, expect } from 'vitest'
import { useModalState } from '@/composables/useModalState'

describe('useModalState - 模态框状态', () => {
  it('初始化时使用传入的初始可见性', () => {
    const modal1 = useModalState(true)
    const modal2 = useModalState(false)

    expect(modal1.visible.value).toBe(true)
    expect(modal2.visible.value).toBe(false)
  })

  it('默认初始可见性为 false', () => {
    const modal = useModalState()
    expect(modal.visible.value).toBe(false)
  })

  it('open 方法设置 visible 为 true', () => {
    const modal = useModalState(false)
    modal.open()
    expect(modal.visible.value).toBe(true)
  })

  it('close 方法设置 visible 为 false', () => {
    const modal = useModalState(true)
    modal.close()
    expect(modal.visible.value).toBe(false)
  })

  it('toggle 方法切换 visible 状态', () => {
    const modal = useModalState(false)
    
    modal.toggle()
    expect(modal.visible.value).toBe(true)
    
    modal.toggle()
    expect(modal.visible.value).toBe(false)
    
    modal.toggle()
    expect(modal.visible.value).toBe(true)
  })

  it('多个实例状态独立', () => {
    const modal1 = useModalState(false)
    const modal2 = useModalState(false)

    modal1.open()
    
    expect(modal1.visible.value).toBe(true)
    expect(modal2.visible.value).toBe(false)
  })
})
