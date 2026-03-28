import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import { logger } from '@/utils/logger'

export interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  userId: string | null
  nickname: string | null
  isAuthenticated: boolean
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const accessToken = ref<string | null>(localStorage.getItem('yumi_access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('yumi_refresh_token'))
  const userId = ref<string | null>(localStorage.getItem('yumi_user_id'))
  const nickname = ref<string | null>(localStorage.getItem('yumi_nickname'))
  const isAuthenticated = computed(() => !!accessToken.value)

  // Actions
  function setTokens(
    newAccessToken: string,
    newRefreshToken: string,
    newUserId: string,
    newNickname?: string
  ) {
    accessToken.value = newAccessToken
    refreshToken.value = newRefreshToken
    userId.value = newUserId
    if (newNickname) {
      nickname.value = newNickname
      localStorage.setItem('yumi_nickname', newNickname)
    }

    localStorage.setItem('yumi_access_token', newAccessToken)
    localStorage.setItem('yumi_refresh_token', newRefreshToken)
    localStorage.setItem('yumi_user_id', newUserId)

    logger.info('AuthStore', 'Tokens set', { userId: newUserId, nickname: newNickname })
  }

  function clearTokens() {
    accessToken.value = null
    refreshToken.value = null
    userId.value = null
    nickname.value = null

    localStorage.removeItem('yumi_access_token')
    localStorage.removeItem('yumi_refresh_token')
    localStorage.removeItem('yumi_user_id')
    localStorage.removeItem('yumi_nickname')

    logger.info('AuthStore', 'Tokens cleared')
  }

  async function validateToken(): Promise<boolean> {
    if (!accessToken.value) {
      logger.info('AuthStore', 'No access token found')
      return false
    }

    try {
      // 尝试获取当前用户信息来验证 token 有效性
      const userInfo = await authApi.getCurrentUser()
      if (userInfo) {
        userId.value = userInfo.userId
        nickname.value = userInfo.nickname
        localStorage.setItem('yumi_user_id', userInfo.userId)
        localStorage.setItem('yumi_nickname', userInfo.nickname)
        logger.info('AuthStore', 'Token validated', { userId: userInfo.userId })
        return true
      }
      return false
    } catch (error) {
      logger.warn('AuthStore', 'Token validation failed', error as Record<string, unknown>)
      return false
    }
  }

  async function refreshAccessToken(): Promise<boolean> {
    if (!refreshToken.value) {
      logger.info('AuthStore', 'No refresh token found')
      return false
    }

    try {
      const response = await authApi.refreshToken(refreshToken.value)
      if (response.accessToken) {
        accessToken.value = response.accessToken
        refreshToken.value = response.refreshToken
        userId.value = response.userId
        localStorage.setItem('yumi_access_token', response.accessToken)
        localStorage.setItem('yumi_refresh_token', response.refreshToken)
        localStorage.setItem('yumi_user_id', response.userId)
        if (response.nickname) {
          nickname.value = response.nickname
          localStorage.setItem('yumi_nickname', response.nickname)
        }
        logger.info('AuthStore', 'Token refreshed successfully', { nickname: response.nickname })
        return true
      }
      return false
    } catch (error) {
      logger.warn('AuthStore', 'Token refresh failed', error as Record<string, unknown>)
      return false
    }
  }

  async function initializeAuth(): Promise<boolean> {
    logger.info('AuthStore', 'Initializing auth')

    // 首先尝试验证现有 token
    if (await validateToken()) {
      return true
    }

    // Token 无效，尝试刷新
    if (await refreshAccessToken()) {
      return true
    }

    // 都失败了，清除 token
    clearTokens()
    return false
  }

  function logout() {
    clearTokens()
    logger.info('AuthStore', 'User logged out')
  }

  return {
    // State
    accessToken,
    refreshToken,
    userId,
    nickname,
    isAuthenticated,
    // Actions
    setTokens,
    clearTokens,
    validateToken,
    refreshAccessToken,
    initializeAuth,
    logout,
  }
})
