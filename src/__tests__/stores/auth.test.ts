import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

describe('AuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('初始化时状态正确', () => {
    const store = useAuthStore()
    expect(store.accessToken).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.userId).toBeNull()
    expect(store.nickname).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('setTokens 设置令牌和用户信息', () => {
    const store = useAuthStore()
    store.setTokens('access-token', 'refresh-token', 'user-123', '测试用户')
    
    expect(store.accessToken).toBe('access-token')
    expect(store.refreshToken).toBe('refresh-token')
    expect(store.userId).toBe('user-123')
    expect(store.nickname).toBe('测试用户')
    expect(store.isAuthenticated).toBe(true)
    expect(localStorage.getItem('yumi_access_token')).toBe('access-token')
    expect(localStorage.getItem('yumi_refresh_token')).toBe('refresh-token')
    expect(localStorage.getItem('yumi_user_id')).toBe('user-123')
    expect(localStorage.getItem('yumi_nickname')).toBe('测试用户')
  })

  it('setTokens 没有昵称时不设置昵称', () => {
    const store = useAuthStore()
    store.setTokens('access-token', 'refresh-token', 'user-123')
    
    expect(store.nickname).toBeNull()
    expect(localStorage.getItem('yumi_nickname')).toBeNull()
  })

  it('clearTokens 清除所有令牌和用户信息', () => {
    const store = useAuthStore()
    store.setTokens('access-token', 'refresh-token', 'user-123', '测试用户')
    store.clearTokens()
    
    expect(store.accessToken).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.userId).toBeNull()
    expect(store.nickname).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem('yumi_access_token')).toBeNull()
    expect(localStorage.getItem('yumi_refresh_token')).toBeNull()
    expect(localStorage.getItem('yumi_user_id')).toBeNull()
    expect(localStorage.getItem('yumi_nickname')).toBeNull()
  })

  it('logout 清除所有令牌', () => {
    const store = useAuthStore()
    store.setTokens('access-token', 'refresh-token', 'user-123', '测试用户')
    store.logout()
    expect(store.accessToken).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.userId).toBeNull()
    expect(store.nickname).toBeNull()
  })
})
