import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useThemeStore } from '@/stores/theme'

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

describe('useThemeStore - 主题 Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  it('初始化默认主题为 light', () => {
    const store = useThemeStore()
    expect(store.theme).toBe('light')
  })

  it('setTheme 设置主题并保存到 localStorage', () => {
    const store = useThemeStore()
    store.setTheme('dark')

    expect(store.theme).toBe('dark')
    expect(localStorageMock.setItem).toHaveBeenCalledWith('yumi-theme', 'dark')
  })

  it('initTheme 从 localStorage 加载已保存的主题', () => {
    localStorageMock.getItem.mockReturnValue('dark')
    const store = useThemeStore()

    store.initTheme()

    expect(store.theme).toBe('dark')
  })

  it('initTheme 在没有保存主题时不做任何改变', () => {
    localStorageMock.getItem.mockReturnValue(null)
    const store = useThemeStore()

    const initialTheme = store.theme
    store.initTheme()

    expect(store.theme).toBe(initialTheme)
  })

  it('切换主题时更新 localStorage', () => {
    const store = useThemeStore()

    store.setTheme('dark')
    expect(localStorageMock.setItem).toHaveBeenCalledWith('yumi-theme', 'dark')

    store.setTheme('light')
    expect(localStorageMock.setItem).toHaveBeenCalledWith('yumi-theme', 'light')
  })
})
