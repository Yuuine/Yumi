import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '@/stores/settings'

const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

vi.mock('@/utils/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}))

describe('useSettingsStore - 设置 Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  it('初始化默认设置', () => {
    const store = useSettingsStore()

    expect(store.showReasoning).toBe(true)
    expect(store.verboseTest).toBe(true)
    expect(store.theme).toBe('light')
  })

  it('setShowReasoning 更新设置并保存', () => {
    const store = useSettingsStore()
    store.setShowReasoning(false)

    expect(store.showReasoning).toBe(false)
    expect(localStorageMock.setItem).toHaveBeenCalled()
  })

  it('setVerboseTest 更新设置并保存', () => {
    const store = useSettingsStore()
    store.setVerboseTest(false)

    expect(store.verboseTest).toBe(false)
    expect(localStorageMock.setItem).toHaveBeenCalled()
  })

  it('setTheme 更新设置并保存', () => {
    const store = useSettingsStore()
    store.setTheme('dark')

    expect(store.theme).toBe('dark')
    expect(localStorageMock.setItem).toHaveBeenCalled()
  })

  it('saveSettings 保存所有设置到 localStorage', () => {
    const store = useSettingsStore()
    store.setShowReasoning(false)
    store.setVerboseTest(false)
    store.setTheme('dark')

    localStorageMock.setItem.mockClear()

    store.saveSettings()

    expect(localStorageMock.setItem).toHaveBeenCalled()
  })

  it('loadSettings 从 localStorage 加载已保存的设置', () => {
    const savedSettings = {
      showReasoning: false,
      verboseTest: false,
      theme: 'dark',
    }
    localStorageMock.getItem.mockReturnValue(JSON.stringify(savedSettings))

    const store = useSettingsStore()
    store.loadSettings()

    expect(store.showReasoning).toBe(false)
    expect(store.verboseTest).toBe(false)
    expect(store.theme).toBe('dark')
  })

  it('loadSettings 在没有保存设置时使用默认值', () => {
    localStorageMock.getItem.mockReturnValue(null)

    const store = useSettingsStore()
    store.loadSettings()

    expect(store.showReasoning).toBe(true)
    expect(store.verboseTest).toBe(true)
    expect(store.theme).toBe('light')
  })

  it('loadSettings 在数据无效时使用默认值', () => {
    localStorageMock.getItem.mockReturnValue('invalid-json')

    const store = useSettingsStore()

    expect(() => store.loadSettings()).not.toThrow()
  })

  it('settings 计算属性返回正确的值', () => {
    const store = useSettingsStore()

    store.setShowReasoning(false)
    store.setVerboseTest(false)
    store.setTheme('dark')

    expect(store.settings.showReasoning).toBe(false)
    expect(store.settings.verboseTest).toBe(false)
    expect(store.settings.theme).toBe('dark')
  })
})
