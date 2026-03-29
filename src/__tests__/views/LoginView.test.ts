import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import LoginView from '@/views/LoginView.vue'

vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
  })),
}))

vi.mock('@/stores', () => ({
  useAuthStore: vi.fn(() => ({
    setTokens: vi.fn(),
  })),
}))

vi.mock('@/composables', () => ({
  useToast: vi.fn(() => ({
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  })),
}))

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
  },
}))

vi.mock('@/utils/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}))

vi.mock('@/components/common', () => ({
  PasswordInput: { template: '<div class="password-input"></div>' },
  StarryBackground: { template: '<div class="starry-background"></div>' },
}))

describe('LoginView - 登录页面', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('可以正常渲染登录页面', () => {
      const wrapper = mount(LoginView)
      expect(wrapper.find('.login-page').exists()).toBe(true)
      expect(wrapper.find('.glass-card').exists()).toBe(true)
      expect(wrapper.find('.form').exists()).toBe(true)
    })

    it('显示登录模式的标题', () => {
      const wrapper = mount(LoginView)
      expect(wrapper.find('.title').text()).toBe('欢迎回来')
    })

    it('显示昵称输入框', () => {
      const wrapper = mount(LoginView)
      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
    })

    it('显示密码输入框组件', () => {
      const wrapper = mount(LoginView)
      expect(wrapper.find('.password-input').exists()).toBe(true)
    })

    it('显示提交按钮', () => {
      const wrapper = mount(LoginView)
      expect(wrapper.find('.submit-btn').exists()).toBe(true)
    })

    it('显示切换登录/注册的链接', () => {
      const wrapper = mount(LoginView)
      expect(wrapper.find('.switch').exists()).toBe(true)
    })
  })

  describe('默认模式', () => {
    it('默认是登录模式', () => {
      const wrapper = mount(LoginView)
      expect(wrapper.find('.title').text()).toBe('欢迎回来')
      expect(wrapper.find('.submit-btn').text()).toContain('登录')
    })

    it('登录模式下不显示确认密码输入框', () => {
      const wrapper = mount(LoginView)
      const confirmInput = wrapper.find('.confirm-input')
      expect(confirmInput.classes()).not.toContain('show')
    })
  })
})
