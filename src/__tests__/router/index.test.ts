import { describe, it, expect, vi, beforeEach } from 'vitest'
import { logger } from '@/utils/logger'

vi.mock('@/utils/logger', () => ({
  logger: {
    info: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

describe('router - 路由守卫逻辑', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  function createRouteGuard() {
    return function beforeEach(to: any, from: any, next: any) {
      const accessToken = localStorage.getItem('yumi_access_token')
      const requiresAuth = to.meta?.requiresAuth

      logger.info('Router', 'Navigation', {
        to: to.path,
        from: from.path,
        requiresAuth,
        hasToken: !!accessToken,
      })

      if (requiresAuth && !accessToken) {
        logger.info('Router', 'Redirecting to login')
        next('/login')
        return
      }

      if (to.path === '/login' && accessToken) {
        logger.info('Router', 'Already logged in, redirecting to chat')
        next('/')
        return
      }

      next()
    }
  }

  describe('未登录状态', () => {
    it('未登录时访问 / 重定向到 /login', () => {
      const guard = createRouteGuard()
      const next = vi.fn()

      guard({ path: '/', meta: { requiresAuth: true } }, { path: '/' }, next)

      expect(next).toHaveBeenCalledWith('/login')
    })

    it('未登录时可以访问 /login', () => {
      const guard = createRouteGuard()
      const next = vi.fn()

      guard({ path: '/login', meta: {} }, { path: '/' }, next)

      expect(next).toHaveBeenCalled()
      expect(next).not.toHaveBeenCalledWith('/login')
    })

    it('未登录访问需要认证的路由时记录重定向日志', () => {
      const guard = createRouteGuard()
      const next = vi.fn()

      guard({ path: '/', meta: { requiresAuth: true } }, { path: '/login' }, next)

      expect(logger.info).toHaveBeenCalledWith(
        'Router',
        'Navigation',
        expect.objectContaining({
          to: '/',
          requiresAuth: true,
          hasToken: false,
        })
      )

      expect(logger.info).toHaveBeenCalledWith('Router', 'Redirecting to login')
    })
  })

  describe('已登录状态', () => {
    beforeEach(() => {
      localStorage.setItem('yumi_access_token', 'test-token')
    })

    it('已登录时访问 /login 重定向到 /', () => {
      const guard = createRouteGuard()
      const next = vi.fn()

      guard({ path: '/login', meta: {} }, { path: '/' }, next)

      expect(next).toHaveBeenCalledWith('/')
    })

    it('已登录时可以访问 /', () => {
      const guard = createRouteGuard()
      const next = vi.fn()

      guard({ path: '/', meta: { requiresAuth: true } }, { path: '/login' }, next)

      expect(next).toHaveBeenCalled()
      expect(next).not.toHaveBeenCalledWith('/login')
    })

    it('已登录访问登录页时记录重定向日志', () => {
      const guard = createRouteGuard()
      const next = vi.fn()

      guard({ path: '/login', meta: {} }, { path: '/' }, next)

      expect(logger.info).toHaveBeenCalledWith(
        'Router',
        'Navigation',
        expect.objectContaining({
          to: '/login',
          hasToken: true,
        })
      )

      expect(logger.info).toHaveBeenCalledWith('Router', 'Already logged in, redirecting to chat')
    })

    it('正常路由切换时记录导航日志', () => {
      const guard = createRouteGuard()
      const next = vi.fn()

      guard({ path: '/', meta: { requiresAuth: true } }, { path: '/other' }, next)

      expect(logger.info).toHaveBeenCalledWith(
        'Router',
        'Navigation',
        expect.objectContaining({
          to: '/',
          from: '/other',
          requiresAuth: true,
          hasToken: true,
        })
      )
    })
  })
})
